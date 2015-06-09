from __future__ import unicode_literals
from django.db import models
from django.contrib.contenttypes.fields import GenericRelation
from django.conf import settings
from common.constants import (Stream_TYPE_PROFILE, Stream_TYPE_TAG, TOKEN_TYPE_EMAIL)
from shoutit.models import ConfirmToken
from shoutit.models.base import UUIDModel, LocationMixin
from shoutit.models.stream import StreamMixin, Listen
from shoutit.utils import debug_logger


AUTH_USER_MODEL = getattr(settings, 'AUTH_USER_MODEL')


class AbstractProfile(UUIDModel, StreamMixin, LocationMixin):
    image = models.URLField(max_length=1024, blank=True,
                            default='https://user-image.static.shoutit.com/default_male.jpg')
    video = models.OneToOneField('shoutit.Video', null=True, blank=True, on_delete=models.SET_NULL)

    class Meta(UUIDModel.Meta):
        abstract = True

    def is_listener(self, stream):
        """
        Check whether the user of this profile is listening to this stream or not
        """
        return Listen.objects.filter(listener=self.user, stream=stream).exists()

    @property
    def listening_count(self):
        return {
            'users': Listen.objects.filter(listener=self.user,
                                           stream__type=Stream_TYPE_PROFILE).count(),
            'tags': Listen.objects.filter(listener=self.user, stream__type=Stream_TYPE_TAG).count()
        }

    @property
    def owner(self):
        return self.user


class Profile(AbstractProfile):
    user = models.OneToOneField(AUTH_USER_MODEL, related_name='profile', db_index=True)
    gender = models.CharField(max_length=10, null=True, blank=True)
    birthday = models.DateField(null=True, blank=True)
    bio = models.TextField(blank=True, max_length=512, default='New Shouter!')

    _stream = GenericRelation('shoutit.Stream', related_query_name='profile')

    def __unicode__(self):
        return "{}".format(self.user)

    def update(self, gender=None, birthday=None, bio=None):
        update_fields = []
        if gender:
            self.gender = gender
            update_fields.append('gender')
        if birthday:
            self.birthday = birthday
            update_fields.append('birthday')
        if bio:
            self.birthday = bio
            update_fields.append('bio')
        self.save(update_fields=update_fields)


class LinkedFacebookAccount(UUIDModel):
    user = models.OneToOneField(AUTH_USER_MODEL, related_name='linked_facebook', db_index=True)
    facebook_id = models.CharField(max_length=24, db_index=True, unique=True)
    access_token = models.CharField(max_length=512)
    expires = models.BigIntegerField(default=0)

    def __unicode__(self):
        return unicode(self.user)


class LinkedGoogleAccount(UUIDModel):
    user = models.OneToOneField(AUTH_USER_MODEL, related_name='linked_gplus', db_index=True)
    gplus_id = models.CharField(max_length=64, db_index=True, unique=True)
    credentials_json = models.CharField(max_length=4096)

    def __unicode__(self):
        return unicode(self.user)


class Permission(UUIDModel):
    name = models.CharField(max_length=512, unique=True, db_index=True)

    def __unicode__(self):
        return self.name


class UserPermission(UUIDModel):
    user = models.ForeignKey(AUTH_USER_MODEL, on_delete=models.CASCADE)
    permission = models.ForeignKey('shoutit.Permission', on_delete=models.CASCADE)
    date_given = models.DateTimeField(auto_now_add=True)


from django.db.models.signals import post_save
from django.dispatch import receiver
from rest_framework.authtoken.models import Token


@receiver(post_save, sender='shoutit.User')
def user_post_save(sender, instance=None, created=False, **kwargs):
    action = 'Created' if created else 'Updated'
    debug_logger.debug('{} User: {}'.format(action, instance))
    if created:
        # create auth token
        Token.objects.create(user=instance)

        # create profile
        Profile.objects.create(user=instance)

        # give appropriate permissions
        from shoutit.permissions import (give_user_permissions, INITIAL_USER_PERMISSIONS,
                                         FULL_USER_PERMISSIONS)
        permissions = INITIAL_USER_PERMISSIONS
        if instance.is_activated:
            permissions = FULL_USER_PERMISSIONS
        give_user_permissions(user=instance, permissions=permissions)

        # send signup email
        if not (instance.is_activated or instance.is_test):
            # create email confirmation token and send verification email
            ConfirmToken.objects.create(user=instance, type=TOKEN_TYPE_EMAIL)
        if not instance.is_test and instance.email and '@sale.craigslist.org' not in instance.email:
            instance.send_signup_email()
