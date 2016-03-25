# -*- coding: utf-8 -*-
"""

"""
from __future__ import unicode_literals

import request_id
from django.utils.encoding import force_text
from django.utils.translation import ugettext_lazy as _
from rest_framework import exceptions as drf_exceptions, status
from rest_framework.utils.serializer_helpers import ReturnList, ReturnDict


class ErrorReason(object):
    REQUIRED = 'required'
    INVALID = 'invalid'
    INVALID_IDENTIFIER = 'invalid_identifier'
    INVALID_HEADER = 'invalid_header'
    INVALID_PARAMETER = 'invalid_parameter'
    INVALID_BODY = 'invalid_body'
    INSECURE_CONNECTION = 'insecure_connection'
    BAD_REQUEST = 'bad_request'
    PARSE_ERROR = 'parse_error'
    AUTH_FAILED = 'auth_failed'
    NOT_AUTHENTICATED = 'not_authenticated'
    PERMISSION_DENIED = 'permission_denied'
    NOT_FOUND = 'not_found'
    METHOD_NOT_ALLOWED = 'method_not_allowed'
    UNSUPPORTED_MEDIA_TYPE = 'unsupported_media_type'
    THROTTLED = 'throttled'
    SERVER_ERROR = 'server_error'
ERROR_REASON = ErrorReason()


class ErrorLocationType(object):
    HEADER = 'header'
    PARAMETER = 'parameter'
    BODY = 'body'
ERROR_LOCATION_TYPE = ErrorLocationType()


def _force_text_recursive(data):
    """
    Descend into a nested data structure, forcing any
    lazy translation strings into plain text.
    This modified version keeps tuples as is
    """
    if isinstance(data, (list, tuple)):
        ret = [
            _force_text_recursive(item) for item in data
        ]
        if isinstance(data, ReturnList):
            return ReturnList(ret, serializer=data.serializer)
        if isinstance(data, tuple):
            return tuple(ret)
        return ret
    elif isinstance(data, dict):
        ret = {
            key: _force_text_recursive(value)
            for key, value in data.items()
        }
        if isinstance(data, ReturnDict):
            return ReturnDict(ret, serializer=data.serializer)
        return ret
    return force_text(data)


class ShoutitAPIException(drf_exceptions.APIException):
    """
    Base class for Shoutit API exceptions.
    Should be used *outside* Serializers, in order to prevent confusion with DRF's `ValidationError`.
    Example usage can be inside views, controllers and pagination classes.
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
            self.developer_message = developer_message
        else:
            self.developer_message = self.default_developer_message

        self.request_id = request_id.get_current_request_id()

        if errors is not None:
            self.errors = _force_text_recursive(errors)
        else:
            self.errors = [{'message': self.message}]

    def __str__(self):
        return self.message


class ShoutitSingleAPIException(ShoutitAPIException):
    default_reason = ERROR_REASON.BAD_REQUEST

    def __init__(self, message, developer_message=None, reason=None):
        errors = [{
            'message': force_text(message),
            'reason': reason or self.default_reason
        }]
        super(ShoutitSingleAPIException, self).__init__(message, developer_message or "", errors)


class ShoutitBadRequest(ShoutitSingleAPIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_reason = ERROR_REASON.BAD_REQUEST


class ShoutitSingleValidationError(ShoutitAPIException):
    """
    Base class for validation exceptions that happen outside serializers.
    Subclasses should provide `.location_type`, `.default_message` and possibly `.reason` properties.
    """
    status_code = status.HTTP_400_BAD_REQUEST
    location_type = ERROR_LOCATION_TYPE.BODY
    reason = ERROR_REASON.INVALID
    default_message = "Invalid input"

    def __init__(self, location, message=None, location_type=None, developer_message=None, reason=None):
        errors = [{
            'message': force_text(message or self.default_message),
            'reason': reason or self.reason,
            'location': location,
            'location_type': location_type or self.location_type
        }]
        super(ShoutitSingleValidationError, self).__init__(message, developer_message or "", errors)


class InvalidHeader(ShoutitSingleValidationError):
    location_type = ERROR_LOCATION_TYPE.HEADER


class InvalidParameter(ShoutitSingleValidationError):
    location_type = ERROR_LOCATION_TYPE.PARAMETER


class InvalidBody(ShoutitSingleValidationError):
    location_type = ERROR_LOCATION_TYPE.BODY


class RequiredHeader(ShoutitSingleValidationError):
    location_type = ERROR_LOCATION_TYPE.HEADER
    reason = ERROR_REASON.REQUIRED
    default_message = _("Missing header")


class RequiredParameter(ShoutitSingleValidationError):
    location_type = ERROR_LOCATION_TYPE.PARAMETER
    reason = ERROR_REASON.REQUIRED
    default_message = _("Missing parameter")


class RequiredBody(ShoutitSingleValidationError):
    location_type = ERROR_LOCATION_TYPE.BODY
    reason = ERROR_REASON.REQUIRED
    default_message = _("Missing field")
