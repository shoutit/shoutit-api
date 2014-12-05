"""
Utils that are independent of Apps and their models
"""

from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _
from common.constants import NOT_ALLOWED_USERNAMES


class NotAllowedUsernamesValidator(object):
    message = _('This username can not be used, please choose something else.')
    code = 'invalid'

    def __call__(self, value):
        if value in NOT_ALLOWED_USERNAMES:
            raise ValidationError(self.message, code=self.code)

validate_allowed_usernames = NotAllowedUsernamesValidator()