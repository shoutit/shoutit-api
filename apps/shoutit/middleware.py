from django.dispatch.dispatcher import receiver
from apps.shoutit.permissions import permissions_changed, ConstantPermission, ANONYMOUS_USER_PERMISSIONS
from apps.shoutit.models import UserPermission
from apps.shoutit.tiered_views.views_utils import set_request_language
from common.tagged_cache import TaggedCache
from apps.shoutit.controllers import facebook_controller
from apps.shoutit.utils import ToSeoFriendly, IsSessionHasLocation, getLocationInfoByIP, MapWithPredefinedCity, JsonResponseBadRequest
from apps.shoutit.controllers import user_controller
import apps.shoutit.settings as settings
import json

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
            auth_response = facebook_controller.ExchangeCode(request, request.GET['code'])
            if auth_response:
                facebook_controller.auth(request, auth_response)
            pass


class UserLocationMiddleware(object):
    @staticmethod
    def process_request(request):

        if not IsSessionHasLocation(request) or request.session.has_key('user_renew_location'):
            if not request.user.is_authenticated():
#				ip = utils.getIP(request)
    #			if not request.session.has_key('user_ip')  or request.session['user_ip'] != ip:
                location_info = getLocationInfoByIP(request)
    #			request.session['user_ip'] = location_info['ip']
                mapped_location = MapWithPredefinedCity(location_info['city'])
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
                request.session['user_city_encoded'] =  ToSeoFriendly(unicode.lower(request.session['user_city']))

            if request.session.has_key('user_renew_location'):
                del(request.session['user_renew_location'])


class JsonPostMiddleware(object):
    @staticmethod
    def process_request(request):
        if request.method == 'POST' and request.body is not '' and request.META['CONTENT_TYPE'] == 'application/json':
            request.POST = request.POST.copy()
            try:
                json_post = json.loads(request.body)
            except ValueError, e:
                return JsonResponseBadRequest({'error': 'invalid json format'})
        else:
            pass

@receiver(permissions_changed)
def refresh_permissions_cache(sender, **kwargs):
    permissions = UserPermission.objects.get_user_permissions(kwargs['request'].user)
    permissions = [ConstantPermission.reversed_instances[p] for p in permissions]
    TaggedCache.set('perma|permissions|%s' % kwargs['request'].user.username, permissions, timeout=10 * 356 * 24 * 60 * 60)
    kwargs['request'].user.constant_permissions = permissions