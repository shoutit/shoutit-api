from django.db.utils import DatabaseError
import django.dispatch
from apps.shoutit.constants import Constant
from apps.shoutit.models import Permission
from django.utils.translation import ugettext_lazy as _


class ConstantPermission(Constant):
    counter = 0
    values = {}
    instances = {}
    reversed_instances = {}

    def __init__(self, text, message):
        self.message = message
        try:
            self.permission, created = Permission.objects.get_or_create(name=text)
            self.value = self.permission.pk
            self.__class__.instances[self] = self.permission
            self.__class__.reversed_instances[self.permission] = self
            Constant.__init__(self, text, self.value)
        except DatabaseError, e:
            if Permission._meta.db_table in e.message:
                self.value = 1
                from django import db
                db.close_connection()
            else:
                raise e

permissions_changed = django.dispatch.Signal(providing_args=["request", "permissions"])

PERMISSION_USE_SHOUT_IT = ConstantPermission("USE_SHOUT_IT", _("You're not allowed to use Shoutit"))
PERMISSION_SHOUT_MORE = ConstantPermission("SHOUT_MORE", _("Please, activate your account to add more shouts (check your email for activation link)"))
PERMISSION_SHOUT_REQUEST = ConstantPermission("SHOUT_REQUEST", _("You're not allowed to use make request shouts."))
PERMISSION_SHOUT_OFFER = ConstantPermission("SHOUT_OFFER", _("You're not allowed to use make offer shouts."))
PERMISSION_FOLLOW_TAG = ConstantPermission("FOLLOW_TAG", _("You're not allowed to listen to tags."))
PERMISSION_FOLLOW_USER = ConstantPermission("FOLLOW_USER", _("You're not allowed to listen to users."))
PERMISSION_ACTIVATED = ConstantPermission("ACTIVATED", _("You are not activated yet"))
PERMISSION_SEND_MESSAGE = ConstantPermission("SEND_MESSAGE", _("You are not allowed to send messages."))
PERMISSION_SHOUT_DEAL = ConstantPermission("SHOUT_DEAL", _("You are not allowed to make deal shouts."))
PERMISSION_POST_EXPERIENCE = ConstantPermission("POST_EXPERIENCE", _("You're not allowed to post experiences."))
PERMISSION_SHARE_EXPERIENCE = ConstantPermission("SHARE_EXPERIENCE", _("You're not allowed to share experiences."))
PERMISSION_COMMENT_ON_POST = ConstantPermission("COMMENT_ON_POST", _("You're not allowed to comment on posts."))
PERMISSION_ADD_GALLERY_ITEM = ConstantPermission("ADD_GALLERY_ITEM", _("You're not allowed to add items."))
PERMISSION_REPORT = ConstantPermission("REPORT", _("You're not allowed to use reporting."))

INITIAL_USER_PERMISSIONS = [
    PERMISSION_USE_SHOUT_IT,
    PERMISSION_SHOUT_MORE,
    PERMISSION_SHOUT_REQUEST,
    PERMISSION_SHOUT_OFFER,
    PERMISSION_FOLLOW_TAG
]

ACTIVATED_USER_PERMISSIONS = [
    PERMISSION_ACTIVATED,
    PERMISSION_SHOUT_MORE,
    PERMISSION_FOLLOW_USER,
    PERMISSION_SEND_MESSAGE,
    PERMISSION_POST_EXPERIENCE,
    PERMISSION_SHARE_EXPERIENCE,
    PERMISSION_COMMENT_ON_POST,
    PERMISSION_REPORT,
]

ACTIVATED_BUSINESS_PERMISSIONS = [
    PERMISSION_ACTIVATED,
    PERMISSION_SHOUT_MORE,
    PERMISSION_COMMENT_ON_POST,
    PERMISSION_SEND_MESSAGE,
    PERMISSION_ADD_GALLERY_ITEM,
    PERMISSION_USE_SHOUT_IT,
    PERMISSION_SHOUT_MORE,
    PERMISSION_SHOUT_OFFER,
    PERMISSION_SHOUT_DEAL,
]

ANONYMOUS_USER_PERMISSIONS = [
    PERMISSION_USE_SHOUT_IT,
]