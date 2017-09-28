import re

from django.conf import settings
from django.contrib.auth import user_logged_in
from django.core.cache import cache
from django.utils import timezone
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
        # Todo: Simplify
        user_agent = str(request.META.get('HTTP_USER_AGENT', '').encode('utf8'))
        if 'com.shoutit-iphone' in user_agent or 'com.appunite.shoutit' in user_agent:
            agent = 'ios'
            if 'Alamofire' in user_agent:
                info_re = re.search('.*/([\d.]+) \(.*; build:(\d+); iOS ([\d.]+)\) Alamofire/([\d.]+)', user_agent)
                app_version = info_re.groups()[0] if info_re else None
                build_no = info_re.groups()[1] if info_re else 0
                os_version = info_re.groups()[2] if info_re else None
            else:
                info_re = re.search('.*(com.shoutit-iphone|com.appunite.shoutit).*\((\d+);', user_agent)
                app_version = None
                build_no = info_re.groups()[1] if info_re else 0
                os_version = None
        elif 'com.shoutit.app.android' in user_agent:
            agent = 'android'
            info_re = re.search('com.shoutit.app.android.*\((\d+);', user_agent)
            app_version = None
            build_no = info_re.groups()[0] if info_re else 0
            os_version = None
        elif 'shoutit-web' in user_agent:
            agent = 'web'
            info_re = re.search('shoutit-web \(.+; .+; .+; release-(\d+).*\)', user_agent)
            app_version = None
            build_no = info_re.groups()[0] if info_re else 0
            os_version = None
        else:
            agent = None
            app_version = None
            build_no = 0
            os_version = None

        request.agent = agent
        request.app_version = app_version
        request.build_no = int(build_no)
        request.os_version = os_version


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


class UserAttributesMiddleware(object):
    """
    Updates the user's language and last_login attributes.
    """

    @staticmethod
    def process_response(request, response):
        # The authentication with DRF happens in the views. Since there is no unified place to add middleware for DRF
        # views, we can update the user language on response time instead.
        # At this point the request should be authenticated already, unless something wrong happened before DRF auth.
        # We need to check for user.id to make sure the user exists and was not deleted (test users can be deleted).
        user = getattr(request, 'user', None)

        # Todo: Make less calls to Datebase, Mixpanel, and Pusher
        if user and user.id and user.is_authenticated():
            if request.LANGUAGE_CODE != user.language:
                user.update_language(request.LANGUAGE_CODE)

            last_login_cache_key = f'user-last-login-{user.id}'
            if cache.get(last_login_cache_key) is None:
                cache.set(last_login_cache_key, timezone.now(), settings.USER_LAST_LOGIN_EXPIRY_SECONDS)
                user_logged_in.send(sender=user.__class__, request=request, user=user)

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
