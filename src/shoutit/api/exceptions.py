# -*- coding: utf-8 -*-
"""

"""
from __future__ import unicode_literals
from v3.exceptions import exception_handler as v3_exception_handler
from rest_framework.views import exception_handler as v2_exception_handler


def exception_handler(exc, context):
    """
    Returns the response that should be used for any given exception.

    By default we handle the REST framework `APIException`, and also
    Django's built-in `Http404` and `PermissionDenied` exceptions.

    Any unhandled exceptions may return `None`, which will cause a 500 error
    to be raised.
    """
    version = context['request'].version
    if version == 'v3':
        return v3_exception_handler(exc, context)
    else:
        return v2_exception_handler(exc, context)


