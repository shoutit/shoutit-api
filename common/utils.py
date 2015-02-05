"""
Utils that are independent of Apps and their models
"""
from django.core.validators import BaseValidator, MinLengthValidator
import httplib2
import sys
import re
from datetime import datetime
from schema import SchemaError

from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _, ungettext_lazy

from common.constants import NOT_ALLOWED_USERNAMES


class NotAllowedUsernamesValidator(object):
    message = _('This username can not be used, please choose something else.')
    code = 'invalid'

    def __call__(self, value):
        if value in NOT_ALLOWED_USERNAMES:
            raise ValidationError(self.message, code=self.code)


validate_allowed_usernames = NotAllowedUsernamesValidator()


def check_runserver_address_port():
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

    elif 'wsgi' in sys.argv:
        address_port = sys.argv[-1]
        return address_port.split(':')

    else:
        return '127.0.0.1', '8000'


def check_offline_mood():
    http = httplib2.Http()
    try:
        resp, content = http.request('http://www.google.com')
        return False
    except httplib2.ServerNotFoundError:
        return True


def process_tags(tags):
    if not isinstance(tags, list):
        return []
    processed_tags = []
    for tag in tags:
        if not isinstance(tag, basestring):
            continue
        tag = tag.lower()
        tag = re.sub('[^a-z0-9-]', '', tag)
        tag = re.sub('([-]){2,}', '-', tag)
        tag = tag[1:] if tag.startswith('-') else tag
        tag = tag[0:-1] if tag.endswith('-') else tag

        if len(tag) >= 2:
            processed_tags.append(tag)
    return processed_tags


def date_unix(date):
    return int((date - datetime(1970, 1, 1)).total_seconds())


class SchemaValidator(object):
    compare = lambda self, a, b: a is not b
    clean = lambda self, x: x
    message = _('Ensure this value is %(limit_value)s (it is %(show_value)s).')
    code = 'limit_value'

    def __init__(self, limit_value):
        self.limit_value = limit_value

    def validate(self, value):
        cleaned = self.clean(value)
        params = {'limit_value': self.limit_value, 'show_value': cleaned}
        if self.compare(cleaned, self.limit_value):
            raise SchemaError([], [self.message % params])


class MinLengthSchemaValidator(SchemaValidator):
    compare = lambda self, a, b: a < b
    clean = lambda self, x: len(x)
    message = ungettext_lazy(
        'Ensure this value has at least %(limit_value)d character (it has %(show_value)d).',
        'Ensure this value has at least %(limit_value)d characters (it has %(show_value)d).',
        'limit_value')


class DictKeysValidator(object):
    def __init__(self, keys, all_=True):
        self._keys_set = set(keys)
        self._all = all_

    def validate(self, d, *args, **kwargs):
        intersection_set = self._keys_set.intersection(d.keys())
        if not self._all:
            if bool(intersection_set):
                return d
            else:
                raise SchemaError("none one of these keys is available: %s" % ", ".join(self._keys_set), [])

        else:
            result = self._keys_set == intersection_set
            if not result:
                missing = self._keys_set - intersection_set
                raise SchemaError('missing keys: %s' % ", ".join(missing), [])
            return d
