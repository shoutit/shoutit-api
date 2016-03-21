# -*- coding: utf-8 -*-
"""

"""
from __future__ import unicode_literals

from collections import OrderedDict

from django.conf import settings
from django.core import exceptions as django_exceptions
from django.http import Http404, JsonResponse
from django.utils.translation import ugettext_lazy as _
from rest_framework import exceptions as drf_exceptions, status
from rest_framework.compat import set_rollback
from rest_framework.request import _hasattr
from rest_framework.response import Response

from shoutit.utils import error_logger


def drf_exception_handler(exc, context):
    """
    Returns the response that should be used for any given exception or bad request in v3 views.
    """
    headers = {}
    developer_message = ""
    request_id = None

    if isinstance(exc, drf_exceptions.APIException):
        status_code = exc.status_code
        if getattr(exc, 'auth_header', None):
            headers['WWW-Authenticate'] = exc.auth_header
        if getattr(exc, 'wait', None):
            headers['Retry-After'] = '%d' % exc.wait

        if isinstance(exc.detail, (list, dict)):
            message = "Multiple errors"
            errors = [exc.detail]
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

    data = exception_response_date(status_code, message, developer_message, request_id, errors)
    log_drf_exception(exc, data, status_code, context)
    return exception_response(data, status_code, headers)


def django_exception_handler(response):
    headers = {}
    status_code = response.status_code
    message = _("Error")
    developer_message = ""
    request_id = None
    errors = {}
    data = exception_response_date(status_code, message, developer_message, request_id, errors)
    return exception_response(data, status_code, headers, django=True)


def set_django_response_headers(res, headers):
    if isinstance(headers, dict):
        for header, value in headers.items():
            res[header] = value


def exception_response_date(status_code, message, developer_message, request_id, errors):
    error_data = {
        'error': OrderedDict([
            ('code', status_code),
            ('message', unicode(message)),
            ('developer_message', developer_message),
            ('request_id', request_id),
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
