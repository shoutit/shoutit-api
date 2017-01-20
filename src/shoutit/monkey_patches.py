# -*- coding: utf-8 -*-
"""

"""
from __future__ import unicode_literals

import uuid
from json import JSONEncoder

import request_id
from rest_framework import exceptions, request
from urllib3.contrib import pyopenssl

from shoutit.api.v3.exceptions import _force_text_recursive

# Tell urllib3 to switch the ssl backend to PyOpenSSL to avoid InsecurePlatformWarning
# https://urllib3.readthedocs.org/en/latest/security.html#insecureplatformwarning
pyopenssl.inject_into_urllib3()

# Save the JSONEncoder default function
default_json_encoder_default = JSONEncoder().default


# Monkey Patch all the JSON imports
class ShoutitJSONEncoder(JSONEncoder):
    def default(self, obj):
        from django.db.models.query import QuerySet
        from elasticsearch_dsl import DocType, result
        from django.utils.functional import Promise
        from django.utils.encoding import force_text
        import datetime
        import decimal
        import uuid

        # case: Class
        # if isinstance(obj, Class):
        #     return class_to_str(obj)

        # See "Date Time String Format" in the ECMA-262 specification.
        if isinstance(obj, datetime.datetime):
            r = obj.isoformat()
            if obj.microsecond:
                r = r[:23] + r[26:]
            if r.endswith('+00:00'):
                r = r[:-6] + 'Z'
            return r
        elif isinstance(obj, datetime.date):
            return obj.isoformat()
        elif isinstance(obj, decimal.Decimal):
            return str(obj)
        elif isinstance(obj, uuid.UUID):
            return str(obj)
        if isinstance(obj, QuerySet):
            return list(obj)
        elif isinstance(obj, result.Response):
            return list(obj)
        elif isinstance(obj, DocType):
            return dict(obj)
        elif isinstance(obj, Promise):
            return force_text(obj)
        # Call the saved default function
        return default_json_encoder_default(obj)


# Replace the JSONEncoder default function with a custom one
JSONEncoder.default = ShoutitJSONEncoder().default


# Monkey Patching DRF Request to expose `__getstate__` and `__setstate__` methods.
# Which will make it possible to be pickled / unpickled at anytime eg. inside python_rq worker.

def __getstate__(self):
    request = {
        'path': self.path,
        'method': self.method,
        'META': {k: v for k, v in self.META.items() if isinstance(v, str)},  # keep string keys only
        'user': self.user,
    }
    return {'request': request, 'version': self.version, 'versioning_scheme': self.versioning_scheme}


request.Request.__getstate__ = __getstate__


def __setstate__(self, state):
    from django.http import HttpRequest
    # empty django Request
    request = HttpRequest()
    state_request = state['request']
    # set path, method, META, user
    for key in state_request:
        request.__setattr__(key, state_request[key])
    self._request = request
    self.version = state['version']
    self.versioning_scheme = state['versioning_scheme']


request.Request.__setstate__ = __setstate__


# Monkey Patching django-request-id to generate id's that can be used for Sentry as `event_id`
def patched_generate_request_id():
    return uuid.uuid4().hex


request_id.__dict__['generate_request_id'] = patched_generate_request_id

# Monkey patch DRF _force_text_recursive to use modified version
exceptions.__dict__['_force_text_recursive'] = _force_text_recursive
