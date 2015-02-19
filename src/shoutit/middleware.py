import json

from django.dispatch.dispatcher import receiver
from django.conf import settings
from django.utils import datastructures

from common.constants import DEFAULT_LOCATION
from common.tagged_cache import TaggedCache
from shoutit.permissions import permissions_changed, ConstantPermission, ANONYMOUS_USER_PERMISSIONS
from shoutit.models import UserPermission
from shoutit.tiered_views.views_utils import set_request_language
from shoutit.utils import JsonResponseBadRequest
from shoutit.controllers import facebook_controller


class APIDetectionMiddleware(object):
    @staticmethod
    def process_request(request):
        # todo: collect general info about api and attach to request
        # do not apply on api v2
        if '/api/v2/' in request.META.get('PATH_INFO'):
            return
        request.is_api = "/api/" in request.META.get('PATH_INFO') or "/oauth/" in request.META.get('PATH_INFO')
        request.api_client = request.META.get('HTTP_SHOUTIT_CLIENT', 'other')
        pass


class SetLanguageMiddleware(object):
    @staticmethod
    def process_request(request):
        # do not apply on api v2
        if '/api/v2/' in request.META.get('PATH_INFO'):
            return

        lang = settings.DEFAULT_LANGUAGE_CODE
        if 'lang' in request.GET:
            lang = request.GET['lang']
        elif request.user.is_authenticated():
            lang = TaggedCache.get('perma|language|%s' % request.user.pk)
        else:
            lang = TaggedCache.get('perma|language|%s' % request.session.session_key)
        if lang:
            set_request_language(request, lang)


class UserPermissionsMiddleware(object):
    @staticmethod
    def attach_permissions_to_request(request):
        if request.user.is_authenticated():
            c_permissions = TaggedCache.get('perma|permissions|{}'.format(request.user.pk))
            if not c_permissions:
                permissions = request.user.permissions.all()
                c_permissions = [ConstantPermission.reversed_instances[p] for p in permissions]
                TaggedCache.set('perma|permissions|{}'.format(request.user.pk), c_permissions, timeout=356 * 24 * 60 * 60)
            request.user.constant_permissions = c_permissions
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


class JsonPostMiddleware(object):
    @staticmethod
    def process_request(request):
        # do not apply on api v2
        if '/api/v2/' in request.META.get('PATH_INFO'):
            return

        # add the json_data attribute to all POST requests.
        if request.method in ['POST', 'PUT'] and 'CONTENT_TYPE' in request.META and 'json' in request.META['CONTENT_TYPE']:
            try:
                request.json_data = json.loads(request.body)
                request.json_to_post_fill = True
                request.json_to_post_filled = False
            except ValueError, e:
                return JsonResponseBadRequest({'error': 'invalid json format: ' + e.message})
            except Exception, e:
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


def default_location(request):
    return {'default_location': DEFAULT_LOCATION}


def include_settings(request):
    return {'settings': settings}