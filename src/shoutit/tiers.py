# -*- coding: utf-8 -*-
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponseRedirect, HttpResponseNotAllowed, HttpResponseNotFound
from django.utils.decorators import available_attrs
from django.utils.functional import wraps
from django.utils.translation import ugettext as _

from common.constants import Constant
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


def tiered_view(
    html_renderer=None,
    json_renderer=None,
    methods=None,
    validator=None,
    login_required=False,
    post_login_required=False,
    activation_required=False,
    post_activation_required=False,
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
                    request.validation_result = validation_result
                    result = view(request, *args, **kwargs)

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

            elif html_renderer and not request.is_ajax():
                output = html_renderer(request, result, *args, **kwargs)

            elif json_renderer and request.is_ajax():
                output = json_renderer(request, result, *args, **kwargs)
            else:
                return HttpResponseNotFound()

            return output
        return _wrapper
    return wrapper


def non_cached_view(html_renderer=None, json_renderer=None, methods=None,
                    validator=None, login_required=False, post_login_required=False, activation_required=False,
                    post_activation_required=False, permissions_required=None, business_subscription_required=False):
    return tiered_view(html_renderer=html_renderer, json_renderer=json_renderer,
                       methods=methods, validator=validator, login_required=login_required, post_login_required=post_login_required,
                       activation_required=activation_required, post_activation_required=post_activation_required,
                       permissions_required=permissions_required, business_subscription_required=business_subscription_required)

