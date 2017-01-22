"""
Utils that are independent of Apps and their models
"""
from __future__ import unicode_literals

import collections
import os
import sys
import uuid
from datetime import datetime
from distutils.util import strtobool as stb

import pytz
from common.constants import NOT_ALLOWED_USERNAMES
from django.core.exceptions import ValidationError
from django.utils.deconstruct import deconstructible
from django.utils.translation import ugettext_lazy as _
from pydash import strings, arrays


def get_address_port(using_gunicorn=False):
    return ''  # Todo (Nour) Fix
    if using_gunicorn:
        from gunicorn import bind
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


def process_tag(name, fn=strings.kebab_case):
    if not isinstance(name, str):
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
    processed_tags = arrays.unique(processed_tags)
    return processed_tags


def date_unix(date):
    try:
        return int((date - datetime(1970, 1, 1, tzinfo=pytz.UTC)).total_seconds())
    except TypeError:
        return int((date.replace(tzinfo=pytz.UTC) - datetime(1970, 1, 1, tzinfo=pytz.UTC)).total_seconds())


def utcfromtimestamp(timestamp):
    return datetime.utcfromtimestamp(timestamp).replace(tzinfo=pytz.UTC)


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
class AllowedUsernameValidator(object):
    message = "'%s' can not be used as username, please choose something else."
    code = 'invalid'

    def __call__(self, value):
        if value in NOT_ALLOWED_USERNAMES:
            raise ValidationError(self.message % value, code=self.code)

    def __eq__(self, other):
        return True


validate_allowed_username = AllowedUsernameValidator()


@deconstructible
class UUIDValidator(object):
    message = _("'%(value)s' is not a valid id.")
    code = 'invalid'

    def __init__(self, message=None):
        if message:
            self.message = message

    def __call__(self, value):
        self.validate(value)

    def __eq__(self, other):
        return True

    def validate(self, value):
        try:
            uuid.UUID(value)
        except:
            raise ValidationError(self.message % {'value': value}, code=self.code)


def tmp_file_from_env(env_var):
    tmp_file_name = ''
    if os.environ.get(env_var):
        # create tmp file from ENV var
        from tempfile import NamedTemporaryFile
        import atexit
        tmp_file = NamedTemporaryFile(delete=False)
        tmp_file.write(bytes(os.environ.get(env_var)))
        tmp_file.close()
        tmp_file_name = tmp_file.name

        def unlink_tmp_file():
            os.unlink(tmp_file_name)

        atexit.register(unlink_tmp_file)  # remove file on exit
    return tmp_file_name


def strtobool(val):
    """
    Convert a string representation of truth to True or False.
    Returns False if 'val' is None
    """
    if val is None:
        return False
    return bool(stb(val))
