from __future__ import unicode_literals
from django.contrib.contenttypes.fields import GenericRelation
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from common.constants import (Stream_TYPE_PROFILE, Stream_TYPE_TAG)
from shoutit.models.base import UUIDModel, LocationMixin
from shoutit.models.stream import StreamMixin, Listen
from shoutit.utils import debug_logger, correct_mobile
from shoutit.settings import AUTH_USER_MODEL


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
    mobile = models.CharField(blank=True, max_length=20, default='')

    _stream = GenericRelation('shoutit.Stream', related_query_name='profile')

    def __unicode__(self):
        return "{}".format(self.user)

    def update(self, gender=None, birthday=None, bio=None, mobile=None):
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
        if mobile:
            self.mobile = mobile
            update_fields.append('mobile')
        self.save(update_fields=update_fields)

    def clean(self):
        self.mobile = correct_mobile(self.mobile, self.country)


@receiver(post_save, sender='shoutit.Profile')
def profile_post_save(sender, instance=None, created=False, **kwargs):
    action = 'Created' if created else 'Updated'
    debug_logger.debug('{} Profile: {}'.format(action, instance))


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
