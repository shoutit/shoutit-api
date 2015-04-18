from django.db import models
from django.contrib.contenttypes.fields import GenericRelation
from django.conf import settings

from common.constants import DEFAULT_LOCATION, Stream_TYPE_PROFILE, Stream_TYPE_TAG
from shoutit.models import ConfirmToken
from shoutit.models.base import UUIDModel
from shoutit.models.stream import StreamMixin, Listen

AUTH_USER_MODEL = getattr(settings, 'AUTH_USER_MODEL')


class AbstractProfile(UUIDModel, StreamMixin):
    image = models.URLField(max_length=1024, default='https://s3-eu-west-1.amazonaws.com/shoutit-user-image-original/9ca75a6a-fc7e-48f7-9b25-ec71783c28f5-1428689093983.jpg', blank=True)
    video = models.OneToOneField('shoutit.Video', null=True, blank=True, on_delete=models.SET_NULL)

    # Location attributes
    country = models.CharField(max_length=200, default=DEFAULT_LOCATION['country'], db_index=True)
    city = models.CharField(max_length=200, default=DEFAULT_LOCATION['city'], db_index=True)
    latitude = models.FloatField(default=DEFAULT_LOCATION['latitude'])
    longitude = models.FloatField(default=DEFAULT_LOCATION['longitude'])

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
            'users': Listen.objects.filter(listener=self.user, stream__type=Stream_TYPE_PROFILE).count(),
            'tags': Listen.objects.filter(listener=self.user, stream__type=Stream_TYPE_TAG).count()
        }

    @property
    def owner(self):
        return self.user


class Profile(AbstractProfile):
    user = models.OneToOneField(AUTH_USER_MODEL, related_name='profile', db_index=True)
    gender = models.CharField(max_length=10, null=True)
    birthday = models.DateField(null=True, blank=True)
    bio = models.TextField(blank=True, max_length=512, default='New Shouter!')

    _stream = GenericRelation('shoutit.Stream', related_query_name='profile')

    def __str__(self):
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
    user = models.OneToOneField(AUTH_USER_MODEL, related_name='linked_facebook')
    facebook_id = models.CharField(max_length=24, db_index=True)
    access_token = models.CharField(max_length=512)
    expires = models.BigIntegerField(default=0)


class LinkedGoogleAccount(UUIDModel):
    user = models.OneToOneField(AUTH_USER_MODEL, related_name='linked_gplus')
    credentials_json = models.CharField(max_length=4096)
    gplus_id = models.CharField(max_length=64, db_index=True)


class Permission(UUIDModel):
    name = models.CharField(max_length=512, unique=True, db_index=True)

    def __str__(self):
        return self.name


class UserPermission(UUIDModel):
    user = models.ForeignKey(AUTH_USER_MODEL, on_delete=models.CASCADE)
    permission = models.ForeignKey('shoutit.Permission', on_delete=models.CASCADE)
    date_given = models.DateTimeField(auto_now_add=True)


from django.db.models.signals import post_save
from django.dispatch import receiver
from rest_framework.authtoken.models import Token


@receiver(post_save, sender='shoutit.User')
def create_auth_token(sender, instance=None, created=False, **kwargs):
    if created:
        # create email confirmation token
        ConfirmToken.objects.create(user=instance)

        # create auth token
        Token.objects.create(user=instance)

        # create profile
        Profile.objects.create(user=instance)

        # give user initial permissions
        from shoutit.permissions import give_user_permissions, INITIAL_USER_PERMISSIONS
        give_user_permissions(user=instance, permissions=INITIAL_USER_PERMISSIONS)