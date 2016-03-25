"""

"""
from __future__ import unicode_literals

from collections import OrderedDict

import sys
from django.conf import settings
from django.core import exceptions as django_exceptions
from django.http import Http404, JsonResponse
from django.utils.translation import ugettext_lazy as _
from raven.utils.encoding import force_text
from request_id import get_current_request_id
from rest_framework import exceptions as drf_exceptions, status
from rest_framework.compat import set_rollback
from rest_framework.request import _hasattr
from rest_framework.response import Response

from common.utils import dict_flatten
from shoutit.api.v3.exceptions import ShoutitAPIException, ERROR_REASON, ERROR_LOCATION_TYPE, _force_text_recursive
from shoutit.utils import error_logger

# key: (message, reason)
drf_exceptions_map = {
    drf_exceptions.ParseError: ("Bad request", ERROR_REASON.PARSE_ERROR),
    drf_exceptions.AuthenticationFailed: ("Authentication failed", ERROR_REASON.AUTH_FAILED),
    drf_exceptions.NotAuthenticated: ("Not authenticated", ERROR_REASON.NOT_AUTHENTICATED),
    drf_exceptions.PermissionDenied: ("Action not allowed", ERROR_REASON.PERMISSION_DENIED),
    drf_exceptions.NotFound: ("Resource not found", ERROR_REASON.NOT_FOUND),
    drf_exceptions.MethodNotAllowed: ("Request not allowed", ERROR_REASON.METHOD_NOT_ALLOWED),
    drf_exceptions.UnsupportedMediaType: ("Bad request", ERROR_REASON.UNSUPPORTED_MEDIA_TYPE),
    drf_exceptions.Throttled: ("Too many requests", ERROR_REASON.THROTTLED),
}

# key: (code, message, developer_message, reason)
other_exceptions_map = {
    Http404: (status.HTTP_400_BAD_REQUEST, _('Resource not found.'), "", ERROR_REASON.NOT_FOUND),
    django_exceptions.PermissionDenied: (status.HTTP_403_FORBIDDEN,
                                         _('Permission denied.'), "", ERROR_REASON.PERMISSION_DENIED)
}


def drf_exception_handler(exc, context):
    """
    Returns the response that should be used for any given exception or bad request in v3 views.
    """
    headers = {}
    developer_message = ""

    if isinstance(exc, ShoutitAPIException):
        status_code = exc.status_code
        message = exc.message
        developer_message = exc.developer_message
        errors = exc.errors

    elif isinstance(exc, drf_exceptions.APIException):
        status_code = exc.status_code
        reason = ERROR_REASON.BAD_REQUEST if status.is_client_error(status_code) else ERROR_REASON.INTERNAL_ERROR

        if getattr(exc, 'auth_header', None):
            headers['WWW-Authenticate'] = exc.auth_header
        if getattr(exc, 'wait', None):
            headers['Retry-After'] = '%d' % exc.wait

        if exc.__class__ in drf_exceptions_map:
            message, reason = drf_exceptions_map[exc.__class__]
            developer_message = exc.detail
            errors = [{'message': message, 'reason': reason}]

        elif isinstance(exc.detail, dict):
            message = _("Invalid input")
            errors = process_validation_dict_errors(exc.detail)

        else:
            message = exc.detail
            errors = [{'message': message, 'reason': reason}]

    elif exc.__class__ in other_exceptions_map:
        status_code, message, developer_message, reason = other_exceptions_map[exc.__class__]
        errors = [{'message': message, 'developer_message': developer_message, 'reason': reason}]

    else:
        if settings.DEBUG and not settings.FORCE_SENTRY:
            return None
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        message = _('Server Error, try again later.')
        developer_message = unicode(exc)
        errors = [{'message': message}]

    data = exception_response_date(status_code, message, developer_message, errors)
    log_drf_exception(exc, data, status_code, context)
    return exception_response(data, status_code, headers)


def process_validation_dict_errors(detail, parent_key='', sep='.'):
    errors = []
    # Flatten the errors dict not to worry about errors of nested fields
    items = dict_flatten(detail, sep=sep).items()
    for key, value in items:
        key = key.replace('non_field_errors', '').replace('..', '.')
        error_location_type = ERROR_LOCATION_TYPE.BODY
        error_reason = ERROR_REASON.INVALID

        # List
        if isinstance(value, list):
            # List of strings
            # raise ValidationError({'username': ["Error message 1", "Error message 2"]
            if all(isinstance(item, basestring) for item in value):
                error_message = value

            # List of dicts (sub errors)
            # raise ValidationError('attachments': [{'location': {'latitude': ["Error message"]}}, {'shout': ["Error message"]}])
            elif all(isinstance(item, dict) for item in value):
                i = 0
                for item in value:
                    errors.extend(process_validation_dict_errors(item, key + sep + str(i)))
                    i += 1
                continue

            # List with single tuple ([message], reason)
            # raising such exception *inside* a field or serializer
            # raise ValidationError((["Only one of `apns` or `gcm` is required not both"], 'required'))
            # or more complicated *outside* fields or serializers
            # raise ValidationError({'field': [(["Error message"], 'invalid')]})
            elif len(value) == 1 and isinstance(value[0], tuple):
                error_message, error_reason = value[0]

            # Ignore other kinds of lists
            else:
                continue

        # String
        # raise ValidationError({'field': "Error message"})
        elif isinstance(value, basestring):
            error_message = value

        # Tuple ([message], reason)
        # raise ValidationError({'field': (["Error message"], 'invalid')})
        elif isinstance(value, tuple):
            error_message, error_reason = value

        # Unknown exception detail schema, log that!
        else:
            error_logger.warning("Unexpected exception detail", extra={'detail': detail})
            continue

        key = parent_key + sep + key if parent_key else key
        if key.endswith('.'):
            key = key[:-1]
        error = {
            'location': key,
            'location_type': error_location_type,
            'reason': error_reason,
            'message': error_message
        }
        errors.append(error)
    return errors


def django_exception_handler(response):
    exc = sys.exc_info()[1]
    if any(map(lambda c: isinstance(exc, c), other_exceptions_map.keys())):
        status_code, message, developer_message, reason = (None, None, None, None)
        for other_exception, value in other_exceptions_map.items():
            if isinstance(exc, other_exception):
                status_code, message, developer_message, reason = value
                break
    else:
        status_code = response.status_code
        if status.is_server_error(status_code):
            message = _("Server Error, try again later")
            reason = ERROR_REASON.INTERNAL_ERROR
        else:
            message = _("Bad request")
            reason = ERROR_REASON.BAD_REQUEST
        if exc:
            developer_message = "%s: %s" % (exc.__class__.__name__, str(exc))
        else:
            developer_message = getattr(response, 'reason_phrase', "Contact server admin with `request_id`")

    errors = [{'message': message, 'reason': reason}]
    data = exception_response_date(status_code, message, developer_message, errors)
    return exception_response(data, status_code, headers={}, django=True)


def set_django_response_headers(res, headers):
    if isinstance(headers, dict):
        for header, value in headers.items():
            res[header] = value


def exception_response_date(status_code, message, developer_message, errors):
    # Return single message for each inner error
    for inner_error in errors:
        if isinstance(inner_error, dict) and isinstance(inner_error.get('message'), list):
            inner_error['message'] = inner_error['message'][0]

    error_data = {
        'error': OrderedDict([
            ('code', status_code),
            ('message', force_text(message)),
            ('developer_message', force_text(developer_message)),
            ('request_id', get_current_request_id()),
            ('errors', _force_text_recursive(errors))
        ])
    }
    return error_data


def exception_response(data, status_code, headers, django=False):
    if django:
        res = JsonResponse(data, status=status_code)
        set_django_response_headers(res, headers)
    else:
        res = Response(data, status=status_code, headers=headers)
    res.is_final = True
    set_rollback()
    return res


def log_drf_exception(exc, data, status_code, context):
    drf_request = context['request']
    django_request = drf_request._request

    if _hasattr(drf_request, '_full_data'):
        # Parsed and should have `raw_body` as it would be set by `ShoutitJsonParser`
        body = getattr(django_request, 'raw_body', None)
    else:
        body = django_request.body

    if hasattr(drf_request.auth, 'client'):
        # Authorized (AccessToken) DRF requests
        client = drf_request.auth.client.name
    elif hasattr(drf_request.auth, 'key'):
        # Authorized (Token) DRF requests
        client = 'Token'
    elif hasattr(drf_request, 'client'):
        # Requests to `access_token` endpoint
        client = drf_request.client.name
    else:
        client = None

    view_name = context['view'].__class__.__name__
    view_action = getattr(context['view'], 'action', 'None')
    exc_name = exc.__class__.__name__
    msg = "%s:%s:%s -> %s" % (drf_request.version, view_name, view_action, exc_name)
    extra = {
        'request': django_request,
        'request_body': body,
        'response_data': data,
        'tags': {
            'api_client': client
        }
    }

    if status.is_server_error(status_code):
        error_logger.error(msg, extra=extra, exc_info=True)
    else:
        error_logger.debug(msg, extra=extra, exc_info=True)
