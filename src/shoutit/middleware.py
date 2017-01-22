from __future__ import unicode_literals

import re

from django.conf import settings
from ipware.ip import get_real_ip

from common.constants import DEFAULT_LOCATION
from shoutit.controllers import facebook_controller
from shoutit.utils import error_logger


class XForwardedForMiddleware(object):
    @staticmethod
    def process_request(request):
        if 'HTTP_X_FORWARDED_FOR' in request.META:
            real_ip = get_real_ip(request)
            if real_ip:
                request.META['REMOTE_ADDR'] = real_ip


class AgentMiddleware(object):
    @staticmethod
    def process_request(request):
        """
        Add information about the request using the its user-agent
        """
        user_agent = str(request.META.get('HTTP_USER_AGENT', '').encode('utf8'))
        if 'com.shoutit-iphone' in user_agent or 'com.appunite.shoutit' in user_agent:
            agent = 'ios'
            build_no_re = re.search('.*(com.shoutit-iphone|com.appunite.shoutit).*\((\d+);', user_agent)
            build_no = build_no_re.groups()[1] if build_no_re else 0
        elif 'com.shoutit.app.android' in user_agent:
            agent = 'android'
            build_no_re = re.search('com.shoutit.app.android.*\((\d+);', user_agent)
            build_no = build_no_re.groups()[0] if build_no_re else 0
        elif 'shoutit-web' in user_agent:
            agent = 'web'
            build_no_re = re.search('shoutit-web \(.+; .+; .+; release-(\d+).*\)', user_agent)
            build_no = build_no_re.groups()[0] if build_no_re else 0
        else:
            agent = None
            build_no = 0

        request.agent = agent
        request.build_no = int(build_no)


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
        from shoutit.permissions import ConstantPermission, ANONYMOUS_USER_PERMISSIONS

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


class UserLanguageMiddleware(object):
    """
    Updates the user's language from information provided by the client.
    """
    @staticmethod
    def process_request(request):
        user = request.user
        if user.is_authenticated() and request.LANGUAGE_CODE != user.language:
            user.update_language(request.LANGUAGE_CODE)

    @staticmethod
    def process_response(request, response):
        # The authentication with DRF happens in the views. Since there is no unified place to add middleware for DRF
        # views, we can update the user language on response time instead.
        # At this point the request should be authenticated already, unless something wrong happened before DRF auth.
        user = getattr(request, 'user', None)
        if user and user.is_authenticated() and request.LANGUAGE_CODE != user.language:
            user.update_language(request.LANGUAGE_CODE)
        return response


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
