from __future__ import unicode_literals
import json

from django.conf import settings
from django.utils import datastructures

from common.constants import DEFAULT_LOCATION
from shoutit.permissions import ConstantPermission, ANONYMOUS_USER_PERMISSIONS
from shoutit.utils import JsonResponseBadRequest
from shoutit.controllers import facebook_controller


class APIDetectionMiddleware(object):
    @staticmethod
    def process_request(request):
        # do not apply on api v2
        if '/v2/' in request.META.get('PATH_INFO'):
            request.is_api = False
            request.api_client = 'other'
            return
        request.is_api = "/api/" in request.META.get('PATH_INFO') or "/oauth/" in request.META.get('PATH_INFO')
        request.api_client = request.META.get('HTTP_SHOUTIT_CLIENT', 'other')
        pass


class UserPermissionsMiddleware(object):
    @staticmethod
    def attach_permissions_to_request(request):
        if request.user.is_authenticated():
            # todo: cache permissions
            permissions = request.user.permissions.all()
            c_permissions = [ConstantPermission.reversed_instances[p] for p in permissions]
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
        if '/v2/' in request.META.get('PATH_INFO'):
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


def default_location(request):
    return {'default_location': DEFAULT_LOCATION}


def include_settings(request):
    return {'settings': settings}
