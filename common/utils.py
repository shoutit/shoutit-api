"""
Utils that are independent of Apps and their models
"""

from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _
from common.constants import NOT_ALLOWED_USERNAMES
import httplib2
import sys


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
    else:
        return '127.0.0.1', '8000'


def check_offline_mood():
    http = httplib2.Http()
    try:
        resp, content = http.request('http://www.google.com')
        return False
    except httplib2.ServerNotFoundError:
        return True
