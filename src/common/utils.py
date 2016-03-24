"""
Utils that are independent of Apps and their models
"""
from __future__ import unicode_literals

import collections
import sys
import uuid
from datetime import datetime

import pytz
import requests
from django.core.exceptions import ValidationError
from django.utils.deconstruct import deconstructible
from pydash import strings

from common.constants import NOT_ALLOWED_USERNAMES


def get_address_port(using_gunicorn=False):
    if using_gunicorn:
        from settings_gunicorn import bind
        return bind.split(':')

    if len(sys.argv) > 1 and sys.argv[1] == "runserver":
        address_port = sys.argv[-1] if len(sys.argv) > 2 else "127.0.0.1:8000"
        if address_port.startswith("-"):
            return
        else:
            try:
                address, port = address_port.split(':')
            except ValueError:
                address, port = '', address_port
        if not address:
            address = '127.0.0.1'
        return address, port

    else:
        return '127.0.0.1', '8000'


def check_offline_mood():
    try:
        # requests.head('http://www.yourapihere.com', timeout=5)
        return False
    except requests.RequestException:
        return True


def process_tag(name, fn=strings.kebab_case):
    if not isinstance(name, basestring):
        return None
    name = fn(name)
    if len(name) < 2:
        return None
    return name


def process_tags(names, snake_case=False):
    processed_tags = []
    fn = strings.snake_case if snake_case else strings.kebab_case
    for name in names:
        processed_tag = process_tag(name, fn)
        if processed_tag:
            processed_tags.append(processed_tag)
    return processed_tags


def date_unix(date):
    try:
        return int((date - datetime(1970, 1, 1, tzinfo=pytz.UTC)).total_seconds())
    except TypeError:
        # Todo: find when this occurs
        return int((date - datetime(1970, 1, 1)).total_seconds())


def any_in(a, b):
    return any(i in b for i in a)


def dict_flatten(d, parent_key='', sep='.'):
    items = []
    for k, v in d.items():
        new_key = parent_key + sep + k if parent_key else k
        if isinstance(v, collections.MutableMapping):
            items.extend(dict_flatten(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)


def json_flatten(y, sep='.'):
    out = {}

    def _flatten(x, name=''):
        if isinstance(x, dict):
            for a in x:
                _flatten(x[a], name + a + sep)
        elif isinstance(x, list):
            i = 0
            for a in x:
                _flatten(a, name + str(i) + sep)
                i += 1
        else:
            out[str(name[:-1])] = str(x)
    _flatten(y)
    return out


@deconstructible
class AllowedUsernamesValidator(object):
    message = "'%s' can not be used as username, please choose something else."
    code = 'invalid'

    def __call__(self, value):
        if value in NOT_ALLOWED_USERNAMES:
            raise ValidationError(self.message % value, code=self.code)

    def __eq__(self, other):
        return True


validate_allowed_usernames = AllowedUsernamesValidator()


@deconstructible
class UUIDValidator(object):
    message = "'%s' is not a valid id."
    code = 'invalid'

    def __call__(self, value):
        UUIDValidator.validate(value)

    def __eq__(self, other):
        return True

    @staticmethod
    def validate(value):
        try:
            uuid.UUID(value)
        except:
            raise ValidationError(UUIDValidator.message % value, code=UUIDValidator.code)
