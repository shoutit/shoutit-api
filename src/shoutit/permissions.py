from django.utils.translation import ugettext_lazy as _
from common.constants import Constant
from shoutit.models import Permission, UserPermission


class ConstantPermission(Constant):
    counter = 0
    values = {}
    reversed_instances = {}

    def __init__(self, text, message):
        self.permission, created = Permission.objects.get_or_create(name=text)
        self.message = message
        self.value = self.permission.id
        self.__class__.reversed_instances[self.permission] = self
        Constant.__init__(self, text, self.value)

    def __hash__(self):
        return self.value.int

    def __int__(self):
        return self.value.int

    def __eq__(self, other):
        return self.value.int == other.value.int


PERMISSION_USE_SHOUTIT = ConstantPermission("USE_SHOUTIT", _("You're not allowed to use Shoutit"))
PERMISSION_SHOUT_MORE = ConstantPermission("SHOUT_MORE", _("Activate your account to create more shouts (check your "
                                                           "email for activation link)"))
PERMISSION_SHOUT_REQUEST = ConstantPermission("SHOUT_REQUEST", _("You're not allowed to create requests"))
PERMISSION_SHOUT_OFFER = ConstantPermission("SHOUT_OFFER", _("You're not allowed to create offers"))
PERMISSION_LISTEN_TO_TAG = ConstantPermission("LISTEN_TO_TAG", _("You're not allowed to listen to interests"))
PERMISSION_LISTEN_TO_PROFILE = ConstantPermission("LISTEN_TO_PROFILE", _("You're not allowed to listen to profiles"))
PERMISSION_SEND_MESSAGE = ConstantPermission("SEND_MESSAGE", _("You are not allowed to send messages"))
PERMISSION_REPORT = ConstantPermission("SEND_REPORT", _("You're not allowed to send reports"))

INITIAL_USER_PERMISSIONS = [
    PERMISSION_USE_SHOUTIT,
    PERMISSION_SHOUT_MORE,
    PERMISSION_SHOUT_REQUEST,
    PERMISSION_SHOUT_OFFER,
    PERMISSION_LISTEN_TO_TAG
]

ACTIVATED_USER_PERMISSIONS = [
    PERMISSION_LISTEN_TO_PROFILE,
    PERMISSION_SEND_MESSAGE,
    PERMISSION_REPORT,
]

FULL_USER_PERMISSIONS = INITIAL_USER_PERMISSIONS + ACTIVATED_USER_PERMISSIONS

ANONYMOUS_USER_PERMISSIONS = [
    PERMISSION_USE_SHOUTIT,
]


def give_user_permissions(user, permissions):
    for permission in permissions:
        if isinstance(permission, ConstantPermission):
            permission = permission.permission
        UserPermission.objects.get_or_create(user=user, permission=permission)


def take_permissions_from_user(user, permissions):
    for permission in permissions:
        if isinstance(permission, ConstantPermission):
            permission = permission.permission
        UserPermission.objects.filter(user=user, permission=permission).delete()
