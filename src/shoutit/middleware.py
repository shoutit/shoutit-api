from __future__ import unicode_literals

from django.conf import settings
from ipware.ip import get_real_ip

from common.constants import DEFAULT_LOCATION
from shoutit.controllers import facebook_controller
from shoutit.permissions import ConstantPermission, ANONYMOUS_USER_PERMISSIONS
from shoutit.utils import error_logger


class XForwardedForMiddleware(object):
    @staticmethod
    def process_request(request):
        if 'HTTP_X_FORWARDED_FOR' in request.META:
            real_ip = get_real_ip(request)
            if real_ip:
                request.META['REMOTE_ADDR'] = real_ip


class BadRequestsMiddleware(object):
    @staticmethod
    def process_response(request, response):
        path = request.path
        excluded_paths = ['/v2/sms', '/v2/misc/sss4']
        if '/v2/' in path and response.status_code in [400] and path not in excluded_paths:
            drf_request = response.renderer_context.get('request') if hasattr(response, 'renderer_context') else None
            req_data = drf_request.data if drf_request else {}
            res_data = getattr(response, 'data', {})
            api_client = drf_request.auth.client.name if drf_request and hasattr(drf_request.auth, 'client') else None
            extra = {
                'request': request,
                'req_data': req_data,
                'res_data': res_data,
                'tags': {
                    'api_client': api_client,
                },
            }
            error_logger.debug("%s: %s" % (request.method.upper(), request.path), extra=extra)
        return response


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


def default_location(request):
    return {'default_location': DEFAULT_LOCATION}


def include_settings(request):
    return {'settings': settings}
