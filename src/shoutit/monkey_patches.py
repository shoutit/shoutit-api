# -*- coding: utf-8 -*-
"""

"""
from __future__ import unicode_literals

import uuid
from json import JSONEncoder

import request_id
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models.query import QuerySet
from django.http import HttpRequest
from django.utils.encoding import force_text
from django.utils.functional import Promise
from elasticsearch_dsl import DocType
from elasticsearch_dsl.result import Response
from rest_framework import exceptions
from rest_framework.request import Request
from urllib3.contrib import pyopenssl

# tell urllib3 to switch the ssl backend to PyOpenSSL to avoid InsecurePlatformWarning
# https://urllib3.readthedocs.org/en/latest/security.html#insecureplatformwarning
from shoutit.api.v3.exceptions import _force_text_recursive

pyopenssl.inject_into_urllib3()


# Monkey Patch all the JSON imports
class ShoutitJSONEncoder(DjangoJSONEncoder):
    def default(self, obj):
        # case: Class
        # if isinstance(obj, Class):
        #     return class_to_str(obj)

        if isinstance(obj, QuerySet):
            return list(obj)
        elif isinstance(obj, Response):
            return list(obj)
        elif isinstance(obj, DocType):
            return dict(obj)
        elif isinstance(obj, Promise):
            return force_text(obj)
        return super(ShoutitJSONEncoder, self).default(obj)


# Replace the JSONEncoder default function with a custom one
JSONEncoder.default = ShoutitJSONEncoder().default


# Monkey Patching DRF Request to expose `__getstate__` and `__setstate__` methods.
# Which will make it possible to be pickled / unpickled at anytime eg. inside python_rq worker.

def __getstate__(self):
    request = {
        'path': self.path,
        'method': self.method,
        'META': {k: v for k, v in self.META.items() if isinstance(v, basestring)},  # keep string keys only
        'user': self.user,
    }
    return {'request': request, 'version': self.version, 'versioning_scheme': self.versioning_scheme}


Request.__getstate__ = __getstate__


def __setstate__(self, state):
    # empty django Request
    request = HttpRequest()
    state_request = state['request']
    # set path, method, META, user
    for key in state_request:
        request.__setattr__(key, state_request[key])
    self._request = request
    self.version = state['version']
    self.versioning_scheme = state['versioning_scheme']


Request.__setstate__ = __setstate__


# Monkey Patching django-request-id to generate id's that can be used for Sentry as `event_id`
def patched_generate_request_id():
    return uuid.uuid4().hex


request_id.__dict__['generate_request_id'] = patched_generate_request_id

# Monkey patch DRF _force_text_recursive to use modified version
exceptions.__dict__['_force_text_recursive'] = _force_text_recursive
