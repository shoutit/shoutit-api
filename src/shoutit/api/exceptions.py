# -*- coding: utf-8 -*-
"""

"""
from raven.contrib.django import DjangoClient
from request_id import get_current_request_id
from rest_framework.exceptions import APIException
from rest_framework.response import Response as DRFResponse
from rest_framework.views import exception_handler as v2_exception_handler

from .v3.views.exception_views import drf_exception_handler as v3_exception_handler, django_exception_handler


def exception_handler(exc, context):
    """
    Returns the response that should be used for any given exception based on the request version.
    """
    view = context['view']
    request = context['request']
    if not hasattr(request, 'version'):
        version, scheme = view.determine_version(request, *view.args, **view.kwargs)
        request.version, request.versioning_scheme = version, scheme

    version = request.version
    if version == 'v3':
        return v3_exception_handler(exc, context)
    else:
        return v2_exception_handler(exc, context)


class APIExceptionMiddleware(object):
    @staticmethod
    def process_response(request, response):
        # Skip processing responses coming from exception handlers
        if getattr(response, 'is_final', False):
            return response
        if 400 <= response.status_code <= 599:
            # DRF Response (API call) e.g. those returned from views directly without raising exceptions
            if isinstance(response, DRFResponse):
                version = response.renderer_context['request'].version
                if version == 'v3':
                    exc = APIException()
                    exc.status_code = response.status_code
                    context = getattr(response, 'renderer_context', {})
                    return v3_exception_handler(exc, context)

            # Django Response (Other call) e.g. those returned by Django on internal server errors
            else:
                return django_exception_handler(response)

        return response


class ShoutitRavenClient(DjangoClient):
    # Override the original `build_msg` to use global request_id using `django-request-id`
    def build_msg(self, *args, **kwargs):
        data = super(ShoutitRavenClient, self).build_msg(*args, **kwargs)
        event_id = get_current_request_id()
        data['event_id'] = event_id
        return data
