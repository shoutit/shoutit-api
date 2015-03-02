# -*- coding: utf-8 -*-

import urlparse
import inspect
import json

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponseRedirect, HttpResponseNotAllowed, HttpResponseNotFound
from django.utils.decorators import available_attrs
from django.utils.functional import wraps
from django.utils.translation import ugettext as _

from common.constants import Constant
from common.tagged_cache import TaggedCache
from shoutit.permissions import PERMISSION_USE_SHOUT_IT
from shoutit.middleware import JsonPostMiddleware


class ResponseResultError(Constant):
    counter = 0
    values = {}

RESPONSE_RESULT_ERROR_NOT_LOGGED_IN = ResponseResultError()
RESPONSE_RESULT_ERROR_404 = ResponseResultError()
RESPONSE_RESULT_ERROR_FORBIDDEN = ResponseResultError()
RESPONSE_RESULT_ERROR_METHOD_NOT_ALLOWED = ResponseResultError()
RESPONSE_RESULT_ERROR_BAD_REQUEST = ResponseResultError()
RESPONSE_RESULT_ERROR_REDIRECT = ResponseResultError()
RESPONSE_RESULT_ERROR_NOT_ACTIVATED = ResponseResultError()
RESPONSE_RESULT_ERROR_PERMISSION_NEEDED = ResponseResultError()


class CacheLevel(Constant):
    counter = 0
    values = {}

CACHE_LEVEL_GLOBAL = CacheLevel()
CACHE_LEVEL_USER = CacheLevel()
CACHE_LEVEL_SESSION = CacheLevel()


class CacheRefreshLevel(Constant):
    counter = 0
    values = {}

CACHE_REFRESH_LEVEL_ALL = CacheRefreshLevel()
CACHE_REFRESH_LEVEL_USER = CacheRefreshLevel()
CACHE_REFRESH_LEVEL_SESSION = CacheRefreshLevel()


class CacheTag(Constant):
    counter = 0
    values = {}

CACHE_TAG_STREAMS = CacheTag(text='Streams')
CACHE_TAG_TAGS = CacheTag(text='tags')
CACHE_TAG_USERS = CacheTag(text='Users')
CACHE_TAG_NOTIFICATIONS = CacheTag(text='Notifications')
CACHE_TAG_MESSAGES = CacheTag(text='Messages')
CACHE_TAG_CURRENCIES = CacheTag(text='Currencies')
CACHE_TAG_DEALS = CacheTag(text='Deals')
CACHE_TAG_VOUCHERS = CacheTag(text='Vouchers')
CACHE_TAG_EXPERIENCES = CacheTag(text='Experiences')
CACHE_TAG_COMMENTS = CacheTag(text='Comments')


class ResponseResult(object):
    """
    Represents the response for a request, it doesn't contain rendering info, just response data.

    Fields:
        errors: A list of errors that are instances of ResponseResultError class.
        messages: A list of 2d tuples, the first entry is the type of the message, and the second entry is the message. e.g. [('info', 'info message'), ('warning', 'warning message')]
        data: A dictionary of data that are passed from the view to the renderer function.
        form_errors: A dictionary of form errors that are passed from the request validator function to the renderer function.
    """

    def __init__(self):
        self.errors = []
        self.messages = []
        self.missing_permissions = []
        self.data = {}
        self.form_errors = {}
        self.__cache = []

    def cache_object(self, obj):
        self.__cache.append(obj)


class ValidationResult(object):
    def __init__(self, valid, form_errors=None, errors=None, messages=None, data=None):
        self.valid = bool(valid)
        self.form_errors = form_errors or {}
        self.errors = errors or []
        self.messages = messages or []
        self.data = data or {}

    def __nonzero__(self):
        return self.valid


def __validate_request(request, methods, validator, *args, **kwargs):
    if request.method in methods:
        if validator:
            return validator(request, *args, **kwargs)
        else:
            return ValidationResult(True)
    return ValidationResult(False, messages=[('error', 'Unsupported request method for this url.')],
                            errors=[RESPONSE_RESULT_ERROR_METHOD_NOT_ALLOWED])


def get_cache_key(request, level):
    key = u'%(address)s•%(user_id)s•%(session_key)s'
    path_parts = urlparse.urlparse(request.build_absolute_uri())
    path = path_parts[2]
    if path_parts[4]:
        path += '?' + '&'.join(sorted(path_parts[4].split('&')))

    key_parameters = {
        'address': path,
        'user_id': '',
        'session_key': '',
    }

    if level == CACHE_LEVEL_SESSION:
        if request.user.is_authenticated():
            key_parameters['user_id'] = str(request.user.pk)
        key_parameters['session_key'] = str(request.session.session_key)
    elif level == CACHE_LEVEL_USER:
        if request.user.is_authenticated():
            key_parameters['user_id'] = str(request.user.pk)
        else:
            key_parameters['session_key'] = str(request.session.session_key)

    return key % key_parameters


def get_cache_tags(request, cache_settings, *args, **kwargs):
    result = cache_settings['tags']
    if cache_settings['dynamic_tags']:
        result.extend(cache_settings['dynamic_tags'](request, *args, **kwargs))
    return result


def tiered_view(
    html_renderer=None,
    json_renderer=None,
    api_renderer=None,
    mobile_renderer=None,
    methods=None,
    validator=None,
    login_required=False,
    post_login_required=False,
    activation_required=False,
    post_activation_required=False,
    cache_settings=None,
    permissions_required=None,
    business_subscription_required=False
):
    if not methods:
        methods = ['GET', 'POST']
    if not permissions_required:
        permissions_required = []

    def wrapper(view=None):
        @wraps(view, assigned=available_attrs(view))
        def _wrapper(request, *args, **kwargs):
            if getattr(request, 'json_to_post_fill', False):
                JsonPostMiddleware.fill_request_post(request)
            result = ResponseResult()

            if PERMISSION_USE_SHOUT_IT not in permissions_required:
                permissions_required.append(PERMISSION_USE_SHOUT_IT)

            if not hasattr(request.user, 'constant_permissions'):
                from shoutit.middleware import UserPermissionsMiddleware
                UserPermissionsMiddleware.attach_permissions_to_request(request)

            if business_subscription_required and request.user.is_authenticated():
                try:
                    profile = request.user.Business
                    groups = request.user.groups
                except ObjectDoesNotExist:
                    profile = groups = None
            else:
                profile = groups = None

            if (login_required and not request.user.is_authenticated()) or (post_login_required and request.method == 'POST' and not request.user.is_authenticated()):
                result.errors.append(RESPONSE_RESULT_ERROR_NOT_LOGGED_IN)

            elif (activation_required and not request.user.is_active) or (post_activation_required and request.method == 'POST' and not request.user.is_active):
                result.errors.append(RESPONSE_RESULT_ERROR_NOT_ACTIVATED)
                result.messages.append(('error', _('You are not activated yet')))

            elif not request.user.is_superuser and permissions_required and not frozenset(permissions_required) <= frozenset(request.user.constant_permissions):
                needed_permissions = frozenset(permissions_required) - frozenset(request.user.constant_permissions)
                result.errors.append(RESPONSE_RESULT_ERROR_PERMISSION_NEEDED)
                for permission in needed_permissions:
                    result.messages.append(('error', permission.message))
                result.missing_permissions = list(needed_permissions)

            elif business_subscription_required and request.user.is_authenticated() and profile and not groups.filter(name__iexact='activebusinesses').count():
                result.messages.append(('error', _('Your subscription has ended.')))
                result.errors.append(RESPONSE_RESULT_ERROR_REDIRECT)
                result.data['next'] = '/subscribe/'

            else:
                validation_result = __validate_request(request, methods, validator, *args, **kwargs)

                if validation_result.valid:
                    if cache_settings:
                        if get_cache_key(request, cache_settings['level']) in TaggedCache:
                            result = TaggedCache.get(get_cache_key(request, cache_settings['level']))
                            cache_settings['to_cache'] = False
                        else:
                            result = None
                            cache_settings['to_cache'] = True
                    else:
                        result = None
                    if not result:
                        request.validation_result = validation_result
                        result = view(request, *args, **kwargs)
                    if result and cache_settings and cache_settings['to_cache']:
                        TaggedCache.set_with_tags(get_cache_key(request, cache_settings['level']), result, get_cache_tags(request, cache_settings, *args, **kwargs), cache_settings['timeout'])

                else:
                    result.errors.extend(validation_result.errors)
                    if RESPONSE_RESULT_ERROR_BAD_REQUEST not in validation_result.errors:
                        result.errors.append(RESPONSE_RESULT_ERROR_BAD_REQUEST)
                    result.form_errors = validation_result.form_errors
                    result.messages.extend(validation_result.messages)

            if RESPONSE_RESULT_ERROR_REDIRECT in result.errors and not request.is_ajax():
                return HttpResponseRedirect(result.data['next'])

            elif RESPONSE_RESULT_ERROR_404 in result.errors:
                return HttpResponseNotFound()

            elif RESPONSE_RESULT_ERROR_METHOD_NOT_ALLOWED in result.errors:
                return HttpResponseNotAllowed(methods)

            elif api_renderer and getattr(request, 'is_api', False):
                response, pre_json_result = api_renderer(request, result, *args, **kwargs)
                response.content = json.dumps(pre_json_result)
                output = response

            elif mobile_renderer and getattr(request, 'flavour', '') == 'mobile':
                output = mobile_renderer(request, result, *args, **kwargs)

            elif html_renderer and not request.is_ajax():
                output = html_renderer(request, result, *args, **kwargs)

            elif json_renderer and request.is_ajax():
                output = json_renderer(request, result, *args, **kwargs)
            else:
                return HttpResponseNotFound()

            return output
        return _wrapper
    return wrapper


def cached_view(level=CACHE_LEVEL_USER, timeout=None, tags=None, dynamic_tags=None, html_renderer=None, json_renderer=None, api_renderer=None,
                mobile_renderer=None, methods=None, validator=None, login_required=False, post_login_required=False,
                activation_required=False, post_activation_required=False, permissions_required=None, business_subscription_required=False):
    if not methods:
        methods = ['GET', 'POST']
    if not permissions_required:
        permissions_required = []
    if not tags:
        tags = []
    if not timeout:
        try:
            timeout = settings.CACHES['default']['TIMEOUT']
        except KeyError:
            try:
                timeout = settings.CACHE_MIDDLEWARE_SECONDS
            except AttributeError:
                timeout = 240

    cache_settings = {
        'timeout': timeout,
        'tags': tags,
        'dynamic_tags': dynamic_tags,
        'level': level
    }

    return tiered_view(html_renderer, json_renderer, api_renderer, mobile_renderer, methods, validator, login_required, post_login_required,
                       activation_required, post_activation_required, cache_settings, permissions_required=permissions_required,
                       business_subscription_required=business_subscription_required)


def non_cached_view(html_renderer=None, json_renderer=None, api_renderer=None, mobile_renderer=None, methods=None,
                    validator=None, login_required=False, post_login_required=False, activation_required=False,
                    post_activation_required=False, permissions_required=None, business_subscription_required=False):
    return tiered_view(html_renderer=html_renderer, json_renderer=json_renderer, api_renderer=api_renderer,mobile_renderer=mobile_renderer,
                       methods=methods, validator=validator, login_required=login_required, post_login_required=post_login_required,
                       activation_required=activation_required, post_activation_required=post_activation_required,
                       permissions_required=permissions_required, business_subscription_required=business_subscription_required)


def refresh_cache(level=CACHE_REFRESH_LEVEL_ALL, tags=None, dynamic_tags=None):
    if not tags:
        tags = []
    def wrapper(view=None):
        @wraps(view, assigned=available_attrs(view))
        def _wrapper(request, *args, **kwargs):
            dirty_tags = get_cache_tags(request, {'tags': tags, 'dynamic_tags': dynamic_tags}, *args, **kwargs)
            _refresh_cache(level, dirty_tags, str(request.session.session_key), request.user.is_authenticated() and str(request.user.pk) or -1)
            return view(request, *args, **kwargs)
        return _wrapper
    return wrapper


def _refresh_cache(level, tags, session_key, user_id):
    if level == CACHE_REFRESH_LEVEL_ALL:
        [TaggedCache.delete_by_tag(tag) for tag in tags]
    elif level == CACHE_LEVEL_SESSION or (level == CACHE_REFRESH_LEVEL_USER and user_id == -1):
        [TaggedCache.delete(key) for tag in tags for key in TaggedCache.get_by_tag(tag).keys() if key.split(u'•')[2] == session_key]
    elif level == CACHE_REFRESH_LEVEL_USER:
        [TaggedCache.delete(key) for tag in tags for key in TaggedCache.get_by_tag(tag).keys() if key.split(u'•')[1] == user_id]


def get_data(tags, function, *args, **kwargs):
    current_frame = inspect.stack()[1][0]
    frame = current_frame.f_back
    if 'timeout' not in frame.f_locals:
        frame = frame.f_back
    if 'timeout' in frame.f_locals and 'key' in frame.f_locals:
        frame_info = inspect.getframeinfo(current_frame)
        key = u'%s•%s•%d•%d' % (frame.f_locals['key'], frame_info.function, frame_info.lineno, frame_info.index)
        if key in TaggedCache:
            result = TaggedCache.get(key)
        else:
            result = function(*args, **kwargs)
            TaggedCache.set_with_tags(key, result, tags, frame.f_locals['timeout'])
    else:
        result = function(*args, **kwargs)
    del frame
    del current_frame
    return result


def refresh_cache_dynamically(tags):
    map(TaggedCache.delete_by_tag, tags)
