# -*- coding: utf-8 -*-
"""

"""
from __future__ import unicode_literals, print_function
import uuid
from json import JSONEncoder
from django.db.models.query import QuerySet
from django.http import HttpRequest
from elasticsearch_dsl import DocType
from elasticsearch_dsl.result import Response
from rest_framework.request import Request

default_json_encoder_default = JSONEncoder().default  # save the JSONEncoder default function


# Monkey Patching all the JSON imports
class ShoutitCustomJSONEncoder(JSONEncoder):
    def default(self, obj):

        # case: UUID
        if isinstance(obj, uuid.UUID):
            return str(obj)

        if isinstance(obj, QuerySet):
            return list(obj)

        if isinstance(obj, Response):
            return list(obj)

        if isinstance(obj, DocType):
            return dict(obj)

        # case: Class
        # if isinstance(obj, Class):
        #     return class_to_str(obj)

        # default:
        return default_json_encoder_default(obj)  # call the saved default function

JSONEncoder.default = ShoutitCustomJSONEncoder().default  # replace the JSONEncoder default function with custom one


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
