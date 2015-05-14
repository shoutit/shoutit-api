from __future__ import unicode_literals
from django.db import models
from shoutit.controllers import email_controller
from shoutit.models import Shout

from shoutit.models.base import UUIDModel, User
from django.conf import settings


class DBCLUser(UUIDModel):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, related_name='%(class)s', unique=True,
                                db_index=True)

    class Meta(UUIDModel.Meta):
        abstract = True

    @property
    def shout(self):
        return Shout.objects.filter(user=self.user)[0]


class CLUser(DBCLUser):
    cl_email = models.EmailField(max_length=254)

    @property
    def cl_ad_id(self):
        return self.cl_email.split('@')[0].split('-')[1]

    def send_invitation_email(self):
        return email_controller.send_cl_invitation_email(self)


class DBUser(DBCLUser):
    db_link = models.URLField(max_length=1000)

    def send_invitation_email(self):
        return email_controller.send_db_invitation_email(self)


class DBZ2User(DBCLUser):
    db_link = models.URLField(max_length=1000)

    def send_invitation_email(self):
        return email_controller.send_db_invitation_email(self)


@property
def cl_user(self):
    try:
        return self.cluser
    except CLUser.DoesNotExist:
        return None
User.add_to_class('cl_user', cl_user)


@property
def db_user(self):
    try:
        return self.dbuser
    except DBUser.DoesNotExist:
        return None
User.add_to_class('db_user', db_user)


@property
def dbz2_user(self):
    try:
        return self.dbz2user
    except DBZ2User.DoesNotExist:
        return None
User.add_to_class('dbz2_user', dbz2_user)


class DBCLConversation(UUIDModel):
    in_email = models.EmailField(max_length=254, null=True, blank=True)
    from_user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='+')
    to_user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='+')
    shout = models.ForeignKey('shoutit.Shout')
    ref = models.CharField(max_length=100, null=True, blank=True)