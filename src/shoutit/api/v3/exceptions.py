# -*- coding: utf-8 -*-
"""

"""
from __future__ import unicode_literals

from collections import OrderedDict

from django.conf import settings
from django.core import exceptions as django_exceptions
from django.http import Http404, JsonResponse
from django.utils.encoding import force_text
from django.utils.translation import ugettext_lazy as _
from request_id import get_current_request_id
from rest_framework import exceptions as drf_exceptions, status
from rest_framework.compat import set_rollback
from rest_framework.exceptions import _force_text_recursive
from rest_framework.request import _hasattr
from rest_framework.response import Response

from common.utils import flatten
from shoutit.utils import error_logger


class ShoutitAPIException(drf_exceptions.APIException):
    """
    Base class for Shoutit API exceptions.
    """
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    default_message = _('A server error occurred.')
    default_developer_message = 'Contact API admin and mention the `request_id`'

    def __init__(self, message=None, developer_message=None, errors=None):
        if message is not None:
            self.message = force_text(message)
        else:
            self.message = force_text(self.default_message)

        if developer_message is not None:
            self.developer_message = force_text(developer_message)

        if errors is not None:
            self.errors = _force_text_recursive(errors)
        else:
            self.errors = [{'message': self.message}]

    def __str__(self):
        return self.message


class ShoutitValidationError(ShoutitAPIException):
    status_code = status.HTTP_400_BAD_REQUEST


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
        if getattr(exc, 'auth_header', None):
            headers['WWW-Authenticate'] = exc.auth_header
        if getattr(exc, 'wait', None):
            headers['Retry-After'] = '%d' % exc.wait

        if isinstance(exc.detail, dict):
            message = _("Invalid input")
            errors = []
            # Flatten the errors dict not to worry about errors of nested fields
            items = flatten(exc.detail).items()
            for key, value in items:
                if '.non_field_errors' in key:
                    key = key.split('.')[0]
                error_location_type = 'body'
                error_reason = 'invalid'

                if isinstance(value, basestring):
                    error_message = value
                elif isinstance(value, list):
                    error_message = ". ".join(value)
                else:
                    error_message = ". ".join(value[0])
                    error_reason = value[1]
                    error_location_type = value[2]

                error = {
                    'location': key,
                    'location_type': error_location_type,
                    'reason': error_reason,
                    'message': error_message
                }
                errors.append(error)
        elif isinstance(exc.detail, list):
            message = exc.detail
            errors = [{'message': unicode(message)}]
        else:
            message = exc.detail
            errors = [{'message': unicode(message)}]

    elif isinstance(exc, Http404):
        status_code = status.HTTP_400_BAD_REQUEST
        message = _('Resource not found.')
        errors = [{'message': unicode(message)}]

    elif isinstance(exc, django_exceptions.PermissionDenied):
        status_code = status.HTTP_403_FORBIDDEN
        message = _('Permission denied.')
        errors = [{'message': unicode(message)}]

    else:
        if settings.DEBUG and not settings.FORCE_SENTRY:
            return None
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        message = _('Server Error, please try again later.')
        developer_message = unicode(exc)
        errors = [{'message': unicode(message)}]

    data = exception_response_date(status_code, message, developer_message, errors)
    log_drf_exception(exc, data, status_code, context)
    return exception_response(data, status_code, headers)


def django_exception_handler(response):
    headers = {}
    status_code = response.status_code
    message = _("Error")
    developer_message = ""
    errors = {}
    data = exception_response_date(status_code, message, developer_message, errors)
    return exception_response(data, status_code, headers, django=True)


def set_django_response_headers(res, headers):
    if isinstance(headers, dict):
        for header, value in headers.items():
            res[header] = value


def exception_response_date(status_code, message, developer_message, errors):
    error_data = {
        'error': OrderedDict([
            ('code', status_code),
            ('message', unicode(message)),
            ('developer_message', developer_message),
            ('request_id', get_current_request_id()),
            ('errors', errors)
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
