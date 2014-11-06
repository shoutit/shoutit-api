from django.dispatch.dispatcher import receiver
from apps.shoutit.permissions import permissions_changed, ConstantPermission, ANONYMOUS_USER_PERMISSIONS
from apps.shoutit.models import UserPermission
from apps.shoutit.tiered_views.views_utils import set_request_language
from common.tagged_cache import TaggedCache
from apps.shoutit.utils import to_seo_friendly, is_session_has_location, get_location_info_by_ip, map_with_predefined_city, JsonResponseBadRequest
from apps.shoutit.controllers import user_controller
from apps.shoutit.controllers import facebook_controller
from django.conf import settings
import json
from django.utils import datastructures


class SetLanguageMiddleware(object):
    @staticmethod
    def process_request(request):
        lang = settings.DEFAULT_LANGUAGE_CODE
        if request.GET.has_key('lang'):
            lang = request.GET['lang']
        elif request.user.is_authenticated():
            lang = TaggedCache.get('perma|language|%d' % request.user.pk)
        else:
            lang = TaggedCache.get('perma|language|%s' % request.session.session_key)
        if lang:
            set_request_language(request, lang)


class UserPermissionsMiddleware(object):
    @staticmethod
    def attach_permissions_to_request(request):
        if request.user.is_authenticated():
            permissions = TaggedCache.get('perma|permissions|%s' % request.user.username)
            if not permissions:
                permissions = UserPermission.objects.get_user_permissions(request.user)
                permissions = [ConstantPermission.reversed_instances[p] for p in permissions]
                TaggedCache.set('perma|permissions|%s' % request.user.username, permissions, timeout=10 * 356 * 24 * 60 * 60)
            request.user.constant_permissions = permissions
        else:
            request.user.constant_permissions = ANONYMOUS_USER_PERMISSIONS

    @staticmethod
    def process_request(request):
        UserPermissionsMiddleware.attach_permissions_to_request(request)


class FBMiddleware(object):
    @staticmethod
    def process_request(request):
    # Check the requests coming from Facebook
        if 'code' in request.GET and 'fb_source' in request.GET:
            auth_response = facebook_controller.exchange_code(request, request.GET['code'])
            if auth_response:
                facebook_controller.user_from_facebook_auth_response(request, auth_response)


class UserLocationMiddleware(object):
    @staticmethod
    def process_request(request):

        if not is_session_has_location(request) or request.session.has_key('user_renew_location'):
            if not request.user.is_authenticated():
#				ip = utils.get_ip(request)
    #			if not request.session.has_key('user_ip')  or request.session['user_ip'] != ip:
                location_info = get_location_info_by_ip(request)
    #			request.session['user_ip'] = location_info['ip']
                mapped_location = map_with_predefined_city(location_info['city'])
                request.session['user_lat'] = mapped_location['latitude']
                request.session['user_lng'] = mapped_location['longitude']
                request.session['user_country'] = mapped_location['country']
                request.session['user_city'] = mapped_location['city']
                request.session['user_city_encoded'] =  mapped_location['city_encoded']
            else:
                profile = user_controller.GetProfile(request.user)
                request.session['user_lat'] = profile and profile.Latitude or 25.2644
                request.session['user_lng'] = profile and profile.Longitude or 55.3117
                request.session['user_country'] = profile and profile.Country or u'AE'
                request.session['user_city'] = profile and profile.City or u'Dubai'
                request.session['user_city_encoded'] = to_seo_friendly(unicode.lower(request.session['user_city']))

            if request.session.has_key('user_renew_location'):
                del(request.session['user_renew_location'])


class JsonPostMiddleware(object):
    @staticmethod
    def process_request(request):
        # add the json_data attribute to all POST requests.
        if request.method == 'POST' and 'application/json' in request.META['CONTENT_TYPE']:
            try:
                request.json_data = json.loads(request.body)
                request.json_to_post_fill = True
                request.json_to_post_filled = False
            except ValueError, e:
                return JsonResponseBadRequest({'error': 'invalid json format: ' + e.message})
            except BaseException, e:
                return JsonResponseBadRequest({'error': e.message})

        elif request.method == 'POST':
            request.json_data = {}
        else:
            pass

    @staticmethod
    def fill_request_post(request, data=None):
        if getattr(request, 'json_to_post_fill', False) and not getattr(request, 'json_to_post_filled', True):
            if not data:
                data = request.json_data
            request.POST = request.POST.copy()
            for item in data:
                request.POST[item] = data[item]

            request._request = datastructures.MergeDict(request.POST, request.GET)
            request.json_to_post_fill = False
            request.json_to_post_filled = True


@receiver(permissions_changed)
def refresh_permissions_cache(sender, **kwargs):
    permissions = UserPermission.objects.get_user_permissions(kwargs['request'].user)
    permissions = [ConstantPermission.reversed_instances[p] for p in permissions]
    TaggedCache.set('perma|permissions|%s' % kwargs['request'].user.username, permissions, timeout=10 * 356 * 24 * 60 * 60)
    kwargs['request'].user.constant_permissions = permissions