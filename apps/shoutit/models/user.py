from itertools import chain
import random
from django.db import models
from django.contrib.auth.models import User
from django.db.models import Min
from django.db.models.signals import post_delete, pre_delete, post_save
from django.dispatch import receiver
from push_notifications.models import APNSDevice, GCMDevice

from apps.shoutit.constants import DEFAULT_LOCATION
# from apps.ActivityLogger.models import Request
from apps.shoutit.models.stream import Stream, Stream2, Stream2Mixin
from apps.shoutit.models.tag import Tag
from apps.shoutit.models.misc import ConfirmToken


class AbstractProfile(models.Model, Stream2Mixin):

    user = models.OneToOneField(User, related_name='%(class)s', unique=True, db_index=True, null=True)

    Image = models.URLField(max_length=1024, null=True)

    # Location attributes
    Country = models.CharField(max_length=200, default=DEFAULT_LOCATION['country'], db_index=True)
    City = models.CharField(max_length=200, default=DEFAULT_LOCATION['city'], db_index=True)
    Latitude = models.FloatField(default=DEFAULT_LOCATION['latitude'])
    Longitude = models.FloatField(default=DEFAULT_LOCATION['longitude'])

    class Meta:
        abstract = True


class Profile(AbstractProfile):
    class Meta:
        app_label = 'shoutit'

    def __unicode__(self):
        return '[UP_' + unicode(self.id) + "] " + unicode(self.user.get_full_name())

    Bio = models.TextField(null=True, max_length=512, default='New Shouter!')
    Mobile = models.CharField(unique=True, null=True, max_length=20)

    # todo: [listen] remove
    Following = models.ManyToManyField(Stream, through='FollowShip')
    Interests = models.ManyToManyField(Tag, related_name='Followers')

    # todo: remove
    Stream = models.OneToOneField(Stream, related_name='OwnerUser', db_index=True)
    #	isBlocked = models.BooleanField(default=False)

    birthday = models.DateField(null=True)
    Sex = models.NullBooleanField(default=True, null=True)

    LastToken = models.ForeignKey(ConfirmToken, null=True, default=None, on_delete=models.SET_NULL)

    isSSS = models.BooleanField(default=False, db_index=True)
    isSMS = models.BooleanField(default=False, db_index=True)

    #	State = models.IntegerField(default = USER_STATE_ACTIVE, db_index=True)

    def GetNotifications(self):
        if not hasattr(self, 'notifications'):
            min_date = self.user.Notifications.filter(ToUser=self.user, IsRead=False).aggregate(min_date=Min('DateCreated'))['min_date']
            if min_date:
                notifications = list(self.user.Notifications.filter(DateCreated__gte=min_date).order_by('-DateCreated'))
                if len(notifications) < 5:
                    notifications = sorted(
                        chain(notifications, list(
                            self.user.Notifications.filter(DateCreated__lt=min_date).order_by('-DateCreated')[:5 - len(notifications)])),
                        key=lambda n: n.DateCreated,
                        reverse=True
                    )
            else:
                notifications = list(self.user.Notifications.filter(IsRead=True).order_by('-DateCreated')[:5])
            self.notifications = notifications
        return self.notifications

    def GetAllNotifications(self):
        if not hasattr(self, 'all_notifications'):
            self.all_notifications = list(self.user.Notifications.order_by('-DateCreated'))
        return self.all_notifications

    def get_unread_notifications_count(self):
        notifications = hasattr(self, 'notifications') and self.notifications
        if not notifications:
            notifications = hasattr(self, 'all_notifications') and self.all_notifications
        if not notifications:
            notifications = self.GetNotifications()
        return len(filter(lambda n: not n.IsRead, notifications))

    def GetTagsCreated(self):
        if not hasattr(self, 'tags_created'):
            self.tags_created = self.TagsCreated.select_related('Creator')
        return self.tags_created

    @property
    def name(self):
        return self.user.get_full_name()

    def __getattribute__(self, name):
        if name in ['username', 'firstname', 'lastname', 'email', 'TagsCreated', 'Shouts', 'get_full_name']:
            return getattr(self.user, name)
        else:
            # return getattr(self, name) < this can't be used here and will cause exit code 138 without any error message!
            return object.__getattribute__(self, name)

    def __setattr__(self, name, value):
        if name in ['username', 'firstname', 'lastname', 'email', 'TagsCreated', 'Shouts', 'get_full_name']:
            setattr(self.user, name, value)
        else:
            object.__setattr__(self, name, value)

    def save(self, *args, **kwargs):
        self.user.save(*args, **kwargs)
        self.user = self.user
        super(Profile, self).save(*args, **kwargs)


@receiver(post_save, sender=Profile)
def attach_user_and_stream(sender, instance, created, raw, using, update_fields, **kwargs):

    # on new profile create stream and attach it
    if created:
        print 'post save on first time'
        # creating the user and attaching it to profile
        # todo: activate it
        # user = User(username=str(random.randint(1000000000, 1999999999)))
        # user.save()
        # instance.user = user
        # instance.save()

        # creating the stream
        stream2 = Stream2(owner=instance)
        stream2.save()


@receiver(pre_delete, sender=Profile)
def delete_attached_stream(sender, instance, using, **kwargs):
    # before deleting remove the stream
    print 'pre_delete'
    instance.stream2.delete()


@receiver(post_delete, sender=Profile)
def delete_attached_user(sender, instance, using, **kwargs):
    # after deleting remove the user
    print 'post_delete'
    instance.user2.delete()


class UserFunctions(object):
    @property
    def abstract_profile(self):
        try:
            return self.profile
        except AttributeError:
            return self.business

    @property
    def name(self):
        if hasattr(self, 'Business') and self.Business:
            return self.Business.Name
        else:
            return self.get_full_name()

    def Image(self):
        if hasattr(self, 'business'):
            return self.business.Image
        elif hasattr(self, 'profile'):
            return self.profile.Image
        else:
            return ''

    def Sex(self):
        profile = Profile.objects.filter(user__id=self.id).values('Sex')
        if profile:
            return profile[0]['Sex']
        else:
            return 'No Profile'

    # def request_count(self):
    #     return Request.objects.filter(user__id=self.id).count()

    def Latitude(self):
        if hasattr(self, 'business'):
            return self.business.Latitude
        elif hasattr(self, 'profile'):
            return self.profile.Latitude
        else:
            return ''

    def Longitude(self):
        if hasattr(self, 'business'):
            return self.business.Longitude
        elif hasattr(self, 'profile'):
            return self.profile.Longitude
        else:
            return ''

    @property
    def apns_device(self):
        if hasattr(self, '_apns_device') and self._apns_device:
            return self._apns_device

        try:
            self._apns_device = APNSDevice.objects.get(user=self)
        except APNSDevice.DoesNotExist:
            self._apns_device = None

        return self._apns_device

    @property
    def gcm_device(self):
        if hasattr(self, '_gcm_device') and self._gcm_device:
            return self._gcm_device

        try:
            self._gcm_device = GCMDevice.objects.get(user=self)
        except GCMDevice.DoesNotExist:
            self._gcm_device = None

        return self._gcm_device


User.__bases__ += (UserFunctions,)


class LinkedFacebookAccount(models.Model):
    class Meta:
        app_label = 'shoutit'

    user = models.OneToOneField(User, related_name='linked_facebook')  # todo: one to one
    Uid = models.CharField(max_length=24, db_index=True)
    AccessToken = models.CharField(max_length=512)
    ExpiresIn = models.BigIntegerField(default=0)


class LinkedGoogleAccount(models.Model):

    user = models.OneToOneField(User, related_name='linked_gplus')  # todo: one to one
    credentials_json = models.CharField(max_length=2048)
    gplus_id = models.CharField(max_length=64, db_index=True)

    class Meta:
        app_label = 'shoutit'


class PermissionsManager(models.Manager):
    @staticmethod
    def get_user_permissions(user):
        return Permission.objects.filter(users=user)


class Permission(models.Model):
    class Meta:
        app_label = 'shoutit'

    def __unicode__(self):
        return self.name

    name = models.CharField(max_length=512, unique=True, db_index=True)
    users = models.ManyToManyField(User, through='UserPermission', related_name='permissions')


class UserPermission(models.Model):
    class Meta:
        app_label = 'shoutit'

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    permission = models.ForeignKey('Permission', on_delete=models.CASCADE)
    date_given = models.DateTimeField(auto_now_add=True)
    objects = PermissionsManager()


# todo: naming: Listen
# todo: move to stream
# todo: reference the user not profile
class FollowShip(models.Model):
    class Meta:
        app_label = 'shoutit'

    def __unicode__(self):
        return unicode(self.id) + ": " + unicode(self.follower) + " @ " + unicode(self.stream)

    follower = models.ForeignKey('Profile')
    stream = models.ForeignKey('Stream')
    date_followed = models.DateTimeField(auto_now_add=True)
    state = models.IntegerField(default=0, db_index=True)


