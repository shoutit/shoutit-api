from itertools import chain

from django.db import models
from django.db.models import Min
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
from django.conf import settings

from common.constants import DEFAULT_LOCATION


# from activity_logger.models import Request
from shoutit.models.base import UUIDModel
from shoutit.models.stream import Stream2Mixin

AUTH_USER_MODEL = getattr(settings, 'AUTH_USER_MODEL')


class AbstractProfile(UUIDModel, Stream2Mixin):
    user = models.OneToOneField(AUTH_USER_MODEL, related_name='%(class)s', unique=True, db_index=True, null=True, blank=True)
    image = models.CharField(max_length=1024, null=True, blank=True)
    video = models.OneToOneField('shoutit.Video', null=True, blank=True, on_delete=models.SET_NULL)

    # Location attributes
    Country = models.CharField(max_length=200, default=DEFAULT_LOCATION['country'], db_index=True)
    City = models.CharField(max_length=200, default=DEFAULT_LOCATION['city'], db_index=True)
    Latitude = models.FloatField(default=DEFAULT_LOCATION['latitude'])
    Longitude = models.FloatField(default=DEFAULT_LOCATION['longitude'])

    class Meta(UUIDModel.Meta):
        abstract = True


class Profile(AbstractProfile):
    Bio = models.TextField(null=True, blank=True, max_length=512, default='New Shouter!')
    Mobile = models.CharField(unique=True, null=True, blank=True, max_length=20)

    # todo: [listen] remove
    Following = models.ManyToManyField('shoutit.Stream', through='shoutit.FollowShip')
    Interests = models.ManyToManyField('shoutit.Tag', related_name='Followers')

    # todo: remove
    Stream = models.OneToOneField('shoutit.Stream', related_name='OwnerUser', db_index=True)
    # isBlocked = models.BooleanField(default=False)

    birthday = models.DateField(null=True, blank=True)
    Sex = models.NullBooleanField()

    LastToken = models.ForeignKey('shoutit.ConfirmToken', null=True, blank=True, default=None, on_delete=models.SET_NULL)

    isSSS = models.BooleanField(default=False, db_index=True)
    isSMS = models.BooleanField(default=False, db_index=True)

    # State = models.IntegerField(default = USER_STATE_ACTIVE, db_index=True)

    def __unicode__(self):
        return '[UP_' + unicode(self.pk) + "] " + unicode(self.user.get_full_name())

    def get_notifications(self):
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

    def get_all_notifications(self):
        if not hasattr(self, 'all_notifications'):
            self.all_notifications = list(self.user.Notifications.order_by('-DateCreated'))
        return self.all_notifications

    def get_unread_notifications_count(self):
        notifications = hasattr(self, 'notifications') and self.notifications
        if not notifications:
            notifications = hasattr(self, 'all_notifications') and self.all_notifications
        if not notifications:
            notifications = self.get_notifications()
        return len(filter(lambda n: not n.IsRead, notifications))

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
        # todo: check! do we really need to save the user on profile save?
        # self.user.save(*args, **kwargs)
        # self.user = self.user
        super(Profile, self).save(*args, **kwargs)


@receiver(post_save)
def attach_user(sender, instance, created, raw, using, update_fields, **kwargs):
    if not issubclass(sender, AbstractProfile):
        return
    # on new profile create stream and attach it
    if created:
        # print 'post save on first time'
        # creating the user and attaching it to profile
        # todo: activate it
        # user = User(username=str(random.randint(1000000000, 1999999999)))
        # user.save()
        # instance.user = user
        # instance.save()
        pass


@receiver(post_delete)
def delete_attached_user(sender, instance, using, **kwargs):
    if not issubclass(sender, AbstractProfile):
        return

    print 'Deleting User for: <%s: %s>' % (sender.__name__, instance)
    instance.user.delete()


class LinkedFacebookAccount(UUIDModel):
    user = models.OneToOneField(AUTH_USER_MODEL, related_name='linked_facebook')
    facebook_id = models.CharField(max_length=24, db_index=True)
    AccessToken = models.CharField(max_length=512)
    ExpiresIn = models.BigIntegerField(default=0)


class LinkedGoogleAccount(UUIDModel):
    user = models.OneToOneField(AUTH_USER_MODEL, related_name='linked_gplus')
    credentials_json = models.CharField(max_length=4096)
    gplus_id = models.CharField(max_length=64, db_index=True)


class PermissionsManager(models.Manager):
    @staticmethod
    def get_user_permissions(user):
        return Permission.objects.filter(users=user)


class Permission(UUIDModel):
    name = models.CharField(max_length=512, unique=True, db_index=True)
    users = models.ManyToManyField(AUTH_USER_MODEL, through='shoutit.UserPermission', related_name='permissions')

    def __unicode__(self):
        return self.name


class UserPermission(UUIDModel):
    user = models.ForeignKey(AUTH_USER_MODEL, on_delete=models.CASCADE)
    permission = models.ForeignKey('shoutit.Permission', on_delete=models.CASCADE)
    date_given = models.DateTimeField(auto_now_add=True)

    objects = PermissionsManager()