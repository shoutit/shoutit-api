# -*- coding: utf-8 -*-
"""

"""
from __future__ import unicode_literals

from django.utils.encoding import force_text
from django.utils.translation import ugettext_lazy as _
from rest_framework import exceptions as drf_exceptions, status
from rest_framework.exceptions import _force_text_recursive


class ErrorReason(object):
    INVALID = 'invalid'
    INVALID_HEADER = 'invalid_header'
    INVALID_PARAMETER = 'invalid_header'
    INVALID_BODY = 'invalid_header'
    REQUIRED = 'required'
ERROR_REASON = ErrorReason()


class ErrorLocationType(object):
    HEADER = 'header'
    PARAMETER = 'parameter'
    BODY = 'body'
ERROR_LOCATION_TYPE = ErrorLocationType()


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
