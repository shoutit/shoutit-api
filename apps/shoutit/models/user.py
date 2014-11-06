from itertools import chain
from django.db import models
from django.contrib.auth.models import User
from django.db.models import Min

from apps.shoutit.models.stream import Stream
from apps.shoutit.models.tag import Tag
from apps.shoutit.models.misc import ConfirmToken
from apps.ActivityLogger.models import Request

class UserProfile(models.Model):
    class Meta:
        app_label = 'shoutit'

    def __unicode__(self):
        return '[UP_' + unicode(self.id) + "] " + unicode(self.User.get_full_name())

    User = models.OneToOneField(User, related_name='Profile', unique=True, db_index=True)
    Image = models.URLField(max_length=1024, null=True)
    Bio = models.TextField(null=True, max_length=512, default='New Shouter!')
    Mobile = models.CharField(unique=True, null=True, max_length=20)

    Following = models.ManyToManyField(Stream, through='FollowShip')
    Interests = models.ManyToManyField(Tag, related_name='Followers')  # todo: interests is extra, following to be used for all

    Stream = models.OneToOneField(Stream, related_name='OwnerUser', db_index=True)
    #	isBlocked = models.BooleanField(default=False)

    # Location attributes
    Country = models.CharField(max_length=200, default='', db_index=True)
    City = models.CharField(max_length=200, default='', db_index=True)
    Latitude = models.FloatField(default=0.0)
    Longitude = models.FloatField(default=0.0)

    Birthdate = models.DateField(null=True)
    Sex = models.NullBooleanField(default=True, null=True)

    LastToken = models.ForeignKey(ConfirmToken, null=True, default=None, on_delete=models.SET_NULL)

    isSSS = models.BooleanField(default=False, db_index=True)
    isSMS = models.BooleanField(default=False, db_index=True)

    #	State = models.IntegerField(default = USER_STATE_ACTIVE, db_index=True)

    #TODO: blocked field

    def GetNotifications(self):
        if not hasattr(self, 'notifications'):
            min_date = self.User.Notifications.filter(ToUser=self.User, IsRead=False).aggregate(min_date=Min('DateCreated'))['min_date']
            if min_date:
                notifications = list(self.User.Notifications.filter(DateCreated__gte=min_date).order_by('-DateCreated'))
                if len(notifications) < 5:
                    notifications = sorted(
                        chain(notifications, list(
                            self.User.Notifications.filter(DateCreated__lt=min_date).order_by('-DateCreated')[:5 - len(notifications)])),
                        key=lambda n: n.DateCreated,
                        reverse=True
                    )
            else:
                notifications = list(self.User.Notifications.filter(IsRead=True).order_by('-DateCreated')[:5])
            self.notifications = notifications
        return self.notifications

    def GetAllNotifications(self):
        if not hasattr(self, 'all_notifications'):
            self.all_notifications = list(self.User.Notifications.order_by('-DateCreated'))
        return self.all_notifications

    def get_unread_notifications_count(self):
        notifications = hasattr(self, 'notifications') and self.notifications
        if not notifications:
            notifications = hasattr(self, 'all_notifications') and self.all_notifications
        if not notifications:
            notifications = self.GetNotifications()
        return len(filter(lambda n: not n.IsRead, notifications))

    def GetInterests(self):
        if not hasattr(self, 'interests'):
            self.interests = self.Interests.select_related('Creator')
        return self.interests

    def GetTagsCreated(self):
        if not hasattr(self, 'tags_created'):
            self.tags_created = self.TagsCreated.select_related('Creator')
        return self.tags_created

    def name(self):
        return self.User.get_full_name()

    def __getattribute__(self, name):
        if name in ['username', 'firstname', 'lastname', 'email', 'TagsCreated', 'Shouts', 'get_full_name']:
            return getattr(self.User, name)
        else:
            # return getattr(self, name) < this can't be used here and will cause exit code 138 without any error message!
            return object.__getattribute__(self, name)

    def __setattr__(self, name, value):
        if name in ['username', 'firstname', 'lastname', 'email', 'TagsCreated', 'Shouts', 'get_full_name']:
            setattr(self.User, name, value)
        else:
            object.__setattr__(self, name, value)

    def save(self, *args, **kwargs):
        self.User.save(*args, **kwargs)
        self.User = self.User
        super(UserProfile,self).save(*args, **kwargs)


class UserFunctions(object):
    #todo: @property
    def name(self):
        if hasattr(self, 'Business') and self.Business:
            return self.Business.Name
        else:
            return self.get_full_name()

    def Image(self):
        if hasattr(self, 'Business'):
            return self.Business.Image
        elif hasattr(self, 'Profile'):
            return self.Profile.Image
        else:
            return ''

    def Sex(self):
        profile = UserProfile.objects.filter(User__id=self.id).values('Sex')
        if profile:
            return profile[0]['Sex']
        else:
            return 'No Profile'

    def request_count(self):
        return Request.objects.filter(user__id=self.id).count()

    def Latitude(self):
        if hasattr(self, 'Business'):
            return self.Business.Latitude
        elif hasattr(self, 'Profile'):
            return self.Profile.Latitude
        else:
            return ''

    def Longitude(self):
        if hasattr(self, 'Business'):
            return self.Business.Longitude
        elif hasattr(self, 'Profile'):
            return self.Profile.Longitude
        else:
            return ''


User.__bases__ += (UserFunctions,)


class LinkedFacebookAccount(models.Model):
    class Meta:
        app_label = 'shoutit'

    User = models.ForeignKey(User, related_name='linked_facebook')
    Uid = models.CharField(max_length=24, db_index=True)
    AccessToken = models.CharField(max_length=512)
    ExpiresIn = models.BigIntegerField(default=0)
    SignedRequest = models.CharField(max_length=1024)     #todo: remove signed request
    link = models.CharField(max_length=128)
    verified = models.BooleanField(default=False)


class LinkedGoogleAccount(models.Model):

    user = models.ForeignKey(User, related_name='linked_google')
    credentials_json = models.CharField(max_length=2048)
    gplus_id = models.CharField(max_length=64, db_index=True)

    #expires_in = models.BigIntegerField(default=0)
    #verified = models.BooleanField(default=False)

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

    follower = models.ForeignKey('UserProfile')
    stream = models.ForeignKey('Stream')
    date_followed = models.DateTimeField(auto_now_add=True)
    state = models.IntegerField(default=0, db_index=True)


