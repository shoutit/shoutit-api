from datetime import timedelta, datetime
from itertools import chain

from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.contrib.contenttypes import generic
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import User
from django.db.models.aggregates import Sum
from django.db.models.query_utils import Q
from django.db.models import Min

# PAUSE: Payment
# from subscription.signals import subscribed, unsubscribed

from apps.ActivityLogger.models import Request
from apps.shoutit import settings
from apps.shoutit.constants import *


class PostManager(models.Manager):
    def GetValidPosts(self, types=[], country_code=None, province_code=None, get_muted=False, get_expired=False):
        q = None
        for i in range(len(types)):
            q = q | Q(Type=types[i]) if i != 0 else Q(Type=types[i])

        post_qs = self.filter(q) if q else self
        if country_code:
            post_qs = post_qs.filter(CountryCode__iexact=country_code)
        if province_code:
            post_qs = post_qs.filter(ProvinceCode__iexact=province_code)
        post_qs = post_qs.distinct().filter(IsDisabled=False)  #.order_by("-DatePublished")
        if not get_muted:
            post_qs = post_qs.filter(IsMuted=False)

        if not get_expired:
            post_qs = self.filter_shout_expired(post_qs)
        return post_qs

    def filter_shout_expired(self, query_set):
        today = datetime.today()
        days = timedelta(days=int(settings.MAX_EXPIRY_DAYS))
        begin = today - days
        query_set = query_set.filter(
            (~Q(Type=POST_TYPE_BUY) & ~Q(Type=POST_TYPE_SELL))
            | (
                (Q(Type=POST_TYPE_BUY) | Q(Type=POST_TYPE_SELL))
                & (
                    Q(shout__ExpiryDate__isnull=True, DatePublished__range=(begin, today))
                    |
                    Q(shout__ExpiryDate__isnull=False, shout__ExpiryDate__gte=today)
                )
            )
        )
        return query_set


class ShoutManager(PostManager):
    def filter_shout_expired(self, query_set):
        today = datetime.today()
        days = timedelta(days=int(settings.MAX_EXPIRY_DAYS))
        begin = today - days
        query_set = query_set.filter(
            Q(ExpiryDate__isnull=True, DatePublished__range=(begin, today)) | Q(ExpiryDate__isnull=False, ExpiryDate__gte=today))
        return query_set

    def GetValidShouts(self, types=[], country_code=None, province_code=None, get_expired=False, get_muted=False):
        if not types: types = [POST_TYPE_SELL, POST_TYPE_BUY, POST_TYPE_DEAL]
        types = [type for type in types if type in [POST_TYPE_SELL, POST_TYPE_BUY, POST_TYPE_DEAL]]
        shout_qs = PostManager.GetValidPosts(self, types, country_code=country_code, province_code=province_code, get_muted=get_muted,
                                             get_expired=get_expired)
        if not get_expired:
            shout_qs = self.filter_shout_expired(shout_qs)
        return shout_qs


class TradeManager(ShoutManager):
    def GetValidTrades(self, types=[], country_code=None, province_code=None, get_expired=False, get_muted=False):
        if not types: types = [POST_TYPE_SELL, POST_TYPE_BUY]
        types = [type for type in types if type in [POST_TYPE_SELL, POST_TYPE_BUY]]
        trade_qs = ShoutManager.GetValidShouts(self, types=types, country_code=country_code, province_code=province_code,
                                               get_expired=get_expired, get_muted=get_muted)

        return trade_qs


class DealManager(ShoutManager):
    def GetValidDeals(self, country_code=None, province_code=None, get_expired=False, get_muted=False):
        deal_qs = ShoutManager.GetValidShouts(self, [POST_TYPE_DEAL], country_code=country_code, province_code=province_code,
                                              get_expired=get_expired, get_muted=get_muted)

        return deal_qs


class ExperienceManager(PostManager):
    def GetValidExperiences(self, country_code=None, province_code=None, get_muted=False):
        experience_qs = PostManager.GetValidPosts(self, types=[POST_TYPE_EXPERIENCE], country_code=country_code,
                                                  province_code=province_code, get_muted=get_muted, get_expired=True)

        return experience_qs


class EventManager(PostManager):
    def GetValidEvents(self, country_code=None, province_code=None, get_muted=False):
        event_qs = PostManager.GetValidPosts(self, types=[POST_TYPE_EVENT], country_code=country_code, province_code=province_code,
                                             get_muted=get_muted, get_expired=True)

        return event_qs


class ConfirmToken(models.Model):
    class Meta:
        app_label = 'shoutit'

    def __unicode__(self):
        return unicode(self.id) + ": " + unicode(self.User) + "::" + self.Token

    Token = models.CharField(max_length=24, db_index=True, unique=True)
    User = models.ForeignKey(User, related_name="Tokens")
    Type = models.IntegerField(default=0)
    DateCreated = models.DateField(auto_now_add=True)
    Email = models.CharField(max_length=128, blank=True)
    IsDisabled = models.BooleanField(default=False, null=False)

    def disable(self):
        self.IsDisabled = True
        self.save()

    @staticmethod
    def getToken(token, get_disabled=True, case_sensitive=True):
        today = datetime.today()
        days = timedelta(days=int(settings.MAX_REG_DAYS))
        begin = today - days
        if case_sensitive:
            t = ConfirmToken.objects.filter(Token__exact=token, DateCreated__gte=begin, DateCreated__lte=today)
        else:
            t = ConfirmToken.objects.filter(Token__iexact=token, DateCreated__gte=begin, DateCreated__lte=today)
        if not get_disabled:
            t = t.filter(IsDisabled=False)
        t = t.select_related(depth=1)
        if len(t) > 0:
            return t[0]
        else:
            return None


class Currency(models.Model):
    class Meta:
        app_label = 'shoutit'

    def __unicode__(self):
        return '[' + self.Code + '] '

    Code = models.CharField(max_length=10)
    Country = models.CharField(max_length=10, blank=True)
    Name = models.CharField(max_length=64, null=True)


class UserProfile(models.Model):
    class Meta:
        app_label = 'shoutit'

    def __unicode__(self):
        return '[UP_' + unicode(self.id) + "] " + unicode(self.User.get_full_name())

    User = models.OneToOneField(User, related_name='Profile', unique=True, db_index=True)
    Image = models.URLField(max_length=1024, null=True)
    Bio = models.TextField(null=True, max_length=512, default='New Shouter!')
    Mobile = models.CharField(unique=True, null=True, max_length=20)

    Following = models.ManyToManyField('Stream', through='FollowShip')
    Interests = models.ManyToManyField('Tag', related_name='Followers')

    Stream = models.OneToOneField('Stream', related_name='OwnerUser', db_index=True)
    #	isBlocked = models.BooleanField(default=False)

    # Location attributes
    Latitude = models.FloatField(default=0.0)
    Longitude = models.FloatField(default=0.0)
    City = models.CharField(max_length=200, default='', db_index=True)
    Country = models.CharField(max_length=200, default='', db_index=True)

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

    def GetUnreadNotificatiosCount(self):
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
            return object.__getattribute__(self, name)

    def __setattr__(self, name, value):
        if name in ['username', 'firstname', 'lastname', 'email', 'TagsCreated', 'Shouts', 'get_full_name']:
            setattr(self.User, name, value)
        else:
            object.__setattr__(self, name, value)

    def save(self, force_insert=False, force_update=False, using=None):
        self.User.save(force_insert, force_update, using)
        self.User = self.User
        models.Model.save(self, force_insert, force_update, using)


class UserFunctions(object):
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

    User = models.ForeignKey(User, related_name='LinkedFB')
    Uid = models.CharField(max_length=24, db_index=True)
    AccessToken = models.CharField(max_length=512)
    ExpiresIn = models.BigIntegerField(default=0)
    SignedRequest = models.CharField(max_length=1024)
    link = models.CharField(max_length=128)
    verified = models.BooleanField(default=False)


class Post(models.Model):
    class Meta:
        app_label = 'shoutit'

    objects = PostManager()

    OwnerUser = models.ForeignKey(User, related_name='Posts')
    Streams = models.ManyToManyField('Stream', related_name='Posts')

    Text = models.TextField(max_length=2000, default='', db_index=True)
    Type = models.IntegerField(default=0, db_index=True)
    DatePublished = models.DateTimeField(auto_now_add=True, db_index=True)

    IsMuted = models.BooleanField(default=False, db_index=True)
    IsDisabled = models.BooleanField(default=False, db_index=True)

    Longitude = models.FloatField(default=0.0)
    Latitude = models.FloatField(default=0.0)
    CountryCode = models.CharField(max_length=2, db_index=True, null=True)
    ProvinceCode = models.CharField(max_length=200, db_index=True, null=True)
    Address = models.CharField(max_length=200, db_index=True, null=True)

    def Mute(self):
        self.IsMuted = True
        self.save()


class Shout(Post):
    class Meta:
        app_label = 'shoutit'

    Tags = models.ManyToManyField('Tag', related_name='Shouts')
    ExpiryDate = models.DateTimeField(null=True, default=None, db_index=True)
    ExpiryNotified = models.BooleanField(default=False)
    objects = ShoutManager()

    def AppendTag(self, tag):
        if not hasattr(self, 'tags'):
            self.tags = []
        self.tags.append(tag)

    def SetTags(self, tags):
        self.tags = tags

    def GetTags(self):
        if hasattr(self, 'tags'):
            return self.tags
        else:
            self.tags = list(self.Tags.all().select_related(depth=2))
            return self.tags

    def GetImages(self):
        if hasattr(self, 'images'):
            return self.images
        else:
            if self.Type == POST_TYPE_EXPERIENCE:
                self.images = list(self.Images.all().order_by('Image'))
            else:
                self.images = self.Item.GetImages()
            return self.images

    def GetFirstImage(self):
        return self.GetImages()[0]

    def SetImages(self, images):
        images = sorted(images, key=lambda img: img.Image)
        self.images = images
        if hasattr(self, 'Item'):
            self.Item.SetImages(images)

    def get_videos(self):
        if hasattr(self, '_videos'):
            return self._videos
        else:
            if self.Type == POST_TYPE_EXPERIENCE:
                self._videos = list(self.videos.all())
            else:
                self._videos = self.Item.get_videos()
            return self._videos

    def set_videos(self, videos):
        self._videos = videos
        if hasattr(self, 'Item'):
            self.Item.set_videos(videos)

    #TODO
    def get_first_video(self):
        pass

    def GetText(self):
        text = ''
        if self.Type == POST_TYPE_BUY or self.Type == POST_TYPE_SELL:
            try:
                text = self.trade.Item.Name + ' ' + self.Text
            except Exception, e:
                print e
        else:
            text = self.Text

        return text

    def is_expired(self):
        now = datetime.now()
        if (not self.ExpiryDate and now > self.DatePublished + timedelta(days=int(settings.MAX_EXPIRY_DAYS))) or (
            self.ExpiryDate and now > self.ExpiryDate):
            return True

    def __unicode__(self):
        return unicode(self.id) + ": " + self.GetText()


class ShoutWrap(models.Model):
    class Meta:
        app_label = 'shoutit'

    def __unicode__(self):
        return unicode(self.id) + ": " + unicode(self.Shout) + " # " + unicode(self.Rank)

    Shout = models.ForeignKey('Shout', related_name='ShoutWraps')
    Stream = models.ForeignKey('Stream', related_name='ShoutWraps')
    Rank = models.FloatField(default=1.0)


class StoredImage(models.Model):
    class Meta:
        app_label = 'shoutit'

    def __unicode__(self):
        return unicode(self.id) + ": " + self.Image + " @ " + unicode(self.Item)

    Shout = models.ForeignKey('Shout', related_name='Images', null=True)
    Item = models.ForeignKey('Item', related_name='Images', null=True)
    Image = models.URLField(max_length=1024)


class StoredFile(models.Model):
    class Meta:
        app_label = 'shoutit'

    def __unicode__(self):
        return "(" + unicode(self.id) + ") " + unicode(self.File)

    User = models.ForeignKey(User, related_name='Documents', null=True)
    File = models.URLField(max_length=1024)
    Type = models.IntegerField()


class Trade(Shout):
    class Meta:
        app_label = 'shoutit'

    def __unicode__(self):
        return unicode(self.id) + ": " + unicode(self.Item)

    Item = models.OneToOneField('Item', related_name='Shout', db_index=True, null=True)
    RelatedStream = models.OneToOneField('Stream', related_name='InitShoutRelated', null=True)
    RecommendedStream = models.OneToOneField('Stream', related_name='InitShoutRecommended', null=True)

    StreamsCode = models.CharField(max_length=2000, default='')
    MaxFollowings = models.IntegerField(default=6)
    MaxDistance = models.FloatField(default=180.0)
    MaxPrice = models.FloatField(default=1.0)
    IsShowMobile = models.BooleanField(default=True)
    IsSSS = models.BooleanField(default=False)
    BaseDatePublished = models.DateTimeField(auto_now_add=True)
    RenewalCount = models.IntegerField(default=0)
    objects = TradeManager()


class Item(models.Model):
    class Meta:
        app_label = 'shoutit'

    def __unicode__(self):
        return unicode(self.id) + ": " + self.Name

    Name = models.CharField(max_length=512, default='')
    Description = models.CharField(max_length=1000, default='')
    Price = models.FloatField(default=0.0)
    Currency = models.ForeignKey(Currency, related_name='Items')
    State = models.IntegerField(default=0, db_index=True)
    DateCreated = models.DateTimeField(auto_now_add=True)

    def GetImages(self):
        if hasattr(self, 'images'):
            return self.images
        else:
            self.images = list(self.Images.all().order_by('Image'))
            return self.images

    def SetImages(self, images):
        images = sorted(images, key=lambda img: img.Image)
        self.images = images

    def GetFirstImage(self):
        return self.GetImages() and self.GetImages()[0] or None

    def get_videos(self):
        if hasattr(self, '_videos'):
            return self._videos
        else:
            self._videos = list(self.videos.all())
            return self._videos

    def set_videos(self, videos):
        self._videos = videos

    #TODO
    def get_first_video(self):
        pass


class Stream(models.Model):
    class Meta:
        app_label = 'shoutit'

    def __unicode__(self):
        return unicode(self.id) + ' ' + self.GetTypeText() + ' (' + unicode(self.GetOwner()) + ')'

    Type = models.IntegerField(default=0, db_index=True)

    def GetOwner(self):
        owner = None
        try:
            if self.Type == STREAM_TYPE_TAG:
                owner = self.OwnerTag
            elif self.Type == STREAM_TYPE_USER:
                owner = self.OwnerUser
            elif self.Type == STREAM_TYPE_BUSINESS:
                owner = self.OwnerBusiness
            elif self.Type == STREAM_TYPE_RECOMMENDED:
                owner = self.InitShoutRecommended
            elif self.Type == STREAM_TYPE_RELATED:
                owner = self.InitShoutRelated
        except Exception, e:
            return None
        return owner

    def GetTypeText(self):
        stream_type = u'None'
        if self.Type == STREAM_TYPE_TAG:
            stream_type = unicode(STREAM_TYPE_TAG)
        elif self.Type == STREAM_TYPE_USER:
            stream_type = unicode(STREAM_TYPE_USER)
        elif self.Type == STREAM_TYPE_BUSINESS:
            stream_type = unicode(STREAM_TYPE_BUSINESS)
        elif self.Type == STREAM_TYPE_RECOMMENDED:
            stream_type = unicode(STREAM_TYPE_RECOMMENDED)
        elif self.Type == STREAM_TYPE_RELATED:
            stream_type = unicode(STREAM_TYPE_RELATED)
        return stream_type

    def PublishShout(self, shout):
        self.Posts.add(shout)
        self.save()

    def UnPublishShout(self, shout):
        self.Posts.remove(shout)
        self.save()


#todo: naming: Listen
class FollowShip(models.Model):
    class Meta:
        app_label = 'shoutit'

    def __unicode__(self):
        return unicode(self.id) + ": " + unicode(self.follower) + " @ " + unicode(self.stream)

    follower = models.ForeignKey(UserProfile)
    stream = models.ForeignKey(Stream)
    date_followed = models.DateTimeField(auto_now_add=True)
    state = models.IntegerField(default=0, db_index=True)


class Tag(models.Model):
    class Meta:
        app_label = 'shoutit'

    def __unicode__(self):
        return unicode(self.id) + ": " + self.Name

    Name = models.CharField(max_length=100, default='', unique=True, db_index=True)
    Creator = models.ForeignKey(User, related_name='TagsCreated', null=True, on_delete=models.SET_NULL)
    Image = models.URLField(max_length=1024, null=True, default='/static/img/shout_tag.png')
    DateCreated = models.DateTimeField(auto_now_add=True)
    Parent = models.ForeignKey('Tag', related_name='ChildTags', blank=True, null=True, db_index=True)

    #	Category = models.ForeignKey(Category, related_name='Tags', null= True, default=None, db_index=True)
    Stream = models.OneToOneField('Stream', related_name='OwnerTag', null=True, db_index=True)
    Definition = models.TextField(null=True, max_length=512, default='New Tag!')

    @property
    def IsCategory(self):
        return True if Category.objects.get(TopTag=self) else False


class Category(models.Model):
    class Meta:
        app_label = 'shoutit'

    def __unicode__(self):
        return self.Name

    Name = models.CharField(max_length=100, default='', unique=True, db_index=True)
    DateCreated = models.DateTimeField(auto_now_add=True)
    TopTag = models.OneToOneField(Tag, related_name='OwnerCategory', null=True)
    Tags = models.ManyToManyField(Tag, related_name='Category')


class Conversation(models.Model):
    class Meta:
        app_label = 'shoutit'

    def __unicode__(self):
        return unicode(self.id)

    FromUser = models.ForeignKey(User, related_name='+')
    ToUser = models.ForeignKey(User, related_name='+')
    AboutPost = models.ForeignKey(Trade, related_name='+')
    #	Text = models.TextField(max_length=256)
    IsRead = models.BooleanField(default=False)
    VisibleToRecivier = models.BooleanField(default=True)
    VisibleToSender = models.BooleanField(default=True)


#	DateCreated = models.DateTimeField(auto_now_add=True)


class Message(models.Model):
    class Meta:
        app_label = 'shoutit'

    def __unicode__(self):
        try:
            return unicode(self.id) + ": " + "(" + unicode(self.FromUser) + " <=>> " + unicode(self.ToUser) + "):" + self.Text
        except:
            return unicode(self.id)

    Conversation = models.ForeignKey(Conversation, related_name='Messages')
    FromUser = models.ForeignKey(User, related_name='ReciviedMessages')
    ToUser = models.ForeignKey(User, related_name='SentMessages')
    #	AboutPost = models.ForeignKey(Post, related_name = 'PostMessages')
    Text = models.TextField()
    IsRead = models.BooleanField(default=False)
    VisibleToRecivier = models.BooleanField(default=True)
    VisibleToSender = models.BooleanField(default=True)
    DateCreated = models.DateTimeField(auto_now_add=True)


class Notification(models.Model):
    class Meta:
        app_label = 'shoutit'

    def __unicode__(self):
        return unicode(self.id) + ": " + self.Text

    ToUser = models.ForeignKey(User, related_name='Notifications')
    FromUser = models.ForeignKey(User, related_name='+', null=True, default=None)
    IsRead = models.BooleanField(default=False)
    Type = models.IntegerField(default=0)
    DateCreated = models.DateTimeField(auto_now_add=True)

    content_type = models.ForeignKey(ContentType, null=True)
    object_pk = models.TextField(null=True)
    AttachedObject = generic.GenericForeignKey(fk_field='object_pk')

    @property
    def Text(self):
        return NotificationType.values[self.Type]

    def MarkAsRead(self):
        self.IsRead = True
        self.save()


class FbContest(models.Model):
    class Meta:
        app_label = 'shoutit'

    ContestId = models.IntegerField(db_index=True)
    User = models.ForeignKey(User, related_name='Contest_1')
    FbId = models.CharField(max_length=24, db_index=True)
    ShareId = models.CharField(max_length=50, null=True, default=None)


class PermissionsManager(models.Manager):
    def get_user_permissions(self, user):
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
    permission = models.ForeignKey(Permission, on_delete=models.CASCADE)
    date_given = models.DateTimeField(auto_now_add=True)
    objects = PermissionsManager()


class BusinessCategoryManager(models.Manager):
    def get_tuples(self):
        return ((c.pk, c.Name) for c in self.all())

    def get_top_level_categories(self):
        return self.filter(Parent=None)


class BusinessCategory(models.Model):
    class Meta:
        app_label = 'shoutit'

    def __unicode__(self):
        return self.PrintHierarchy()

    Name = models.CharField(max_length=1024, db_index=True, null=False)
    Source = models.IntegerField(default=BUSINESS_SOURCE_TYPE_NONE)
    SourceID = models.CharField(max_length=128, blank=True)
    Parent = models.ForeignKey('self', null=True, default=None, related_name='children')

    objects = BusinessCategoryManager()

    def PrintHierarchy(self):
        return unicode('%s > %s' % (self.Parent.PrintHierarchy(), self.Name)) if self.Parent else unicode(self.Name)


class BusinessProfile(models.Model):
    class Meta:
        app_label = 'shoutit'

    def __unicode__(self):
        return '[BP_%s | %s | %s]' % (unicode(self.id), unicode(self.Name), unicode(self.User))

    User = models.OneToOneField(User, related_name='Business', db_index=True)

    Name = models.CharField(max_length=1024, db_index=True, null=False)
    Category = models.ForeignKey(BusinessCategory, null=True, on_delete=models.SET_NULL)

    Image = models.URLField(max_length=1024, null=True)
    About = models.TextField(null=True, max_length=512, default='')
    Phone = models.CharField(unique=True, null=True, max_length=20)
    Website = models.URLField(max_length=1024, null=True)

    Longitude = models.FloatField(default=0.0)
    Latitude = models.FloatField(default=0.0)
    Country = models.CharField(max_length=2, db_index=True, null=True)
    City = models.CharField(max_length=200, db_index=True, null=True)
    Address = models.CharField(max_length=200, db_index=True, null=True)

    Stream = models.OneToOneField('Stream', related_name='OwnerBusiness', null=True, db_index=True)
    LastToken = models.ForeignKey(ConfirmToken, null=True, default=None, on_delete=models.SET_NULL)

    Confirmed = models.BooleanField(default=False)

    def __getattribute__(self, name):
        if name in ['username', 'firstname', 'lastname', 'email', 'TagsCreated', 'Shouts', 'get_full_name', 'is_active']:
            return getattr(self.User, name)
        else:
            return object.__getattribute__(self, name)

    def __setattr__(self, name, value):
        if name in ['username', 'firstname', 'lastname', 'email', 'TagsCreated', 'Shouts', 'get_full_name', 'is_active']:
            setattr(self.User, name, value)
        else:
            object.__setattr__(self, name, value)

    @property
    def Bio(self):
        return self.About

    @Bio.setter
    def Bio(self, value):
        self.About = value


    @property
    def Mobile(self):
        return self.Phone

    @Mobile.setter
    def Mobile(self, value):
        self.Phone = value

    def name(self):
        return self.Name

    def has_source(self):
        try:
            if self.Source:
                return True
            else:
                return False
        except ObjectDoesNotExist, e:
            return False


class BusinessCreateApplication(models.Model):
    class Meta:
        app_label = 'shoutit'

    User = models.ForeignKey(User, related_name='BusinessCreateApplication', null=True, on_delete=models.SET_NULL)
    Business = models.ForeignKey(BusinessProfile, related_name='UserApplications', null=True, on_delete=models.SET_NULL)

    Name = models.CharField(max_length=1024, db_index=True, null=True)
    Category = models.ForeignKey(BusinessCategory, null=True, on_delete=models.SET_NULL)

    Image = models.URLField(max_length=1024, null=True)
    About = models.TextField(null=True, max_length=512, default='')
    Phone = models.CharField(null=True, max_length=20)
    Website = models.URLField(max_length=1024, null=True)

    Longitude = models.FloatField(default=0.0)
    Latitude = models.FloatField(default=0.0)
    Country = models.CharField(max_length=2, db_index=True, null=True)
    City = models.CharField(max_length=200, db_index=True, null=True)
    Address = models.CharField(max_length=200, db_index=True, null=True)

    LastToken = models.ForeignKey(ConfirmToken, null=True, default=None, on_delete=models.SET_NULL)
    DateApplied = models.DateField(auto_now_add=True)

    Status = models.IntegerField(default=int(BUSINESS_CONFIRMATION_STATUS_WAITING), db_index=True)


class BusinessSource(models.Model):
    class Meta:
        app_label = 'shoutit'

    Business = models.OneToOneField(BusinessProfile, related_name="Source")
    Source = models.IntegerField(default=BUSINESS_SOURCE_TYPE_NONE)
    SourceID = models.CharField(max_length=128, blank=True)


class BusinessConfirmation(models.Model):
    class Meta:
        app_label = 'shoutit'

    User = models.ForeignKey(User, related_name='BusinessConfirmations')
    Files = models.ManyToManyField(StoredFile, related_name='Comfirmation')
    DateSent = models.DateTimeField(auto_now_add=True)


class Deal(Shout):
    class Meta:
        app_label = 'shoutit'

    MinBuyers = models.IntegerField(default=0)
    MaxBuyers = models.IntegerField(null=True)
    OriginalPrice = models.FloatField()
    IsClosed = models.BooleanField(default=False)
    Item = models.ForeignKey(Item, related_name='Deals', on_delete=models.SET_NULL, null=True)
    ValidFrom = models.DateTimeField(null=True)
    ValidTo = models.DateTimeField(null=True)
    objects = DealManager()

    def BuyersCount(self):
        return self.Buys.aggregate(buys=Sum('Amount'))['buys']

    def AvailableCount(self):
        return self.MaxBuyers - self.BuyersCount()


class DealBuy(models.Model):
    class Meta:
        app_label = 'shoutit'

    Deal = models.ForeignKey(Deal, related_name='Buys', on_delete=models.SET_NULL, null=True)
    User = models.ForeignKey(User, related_name='DealsBought', on_delete=models.SET_NULL, null=True)
    Amount = models.IntegerField(default=1)
    DateBought = models.DateTimeField(auto_now_add=True)


class Experience(Post):
    class Meta:
        app_label = 'shoutit'

    def __unicode__(self):
        return unicode(self.id)

    AboutBusiness = models.ForeignKey('BusinessProfile', related_name='Experiences')
    State = models.IntegerField(null=False)
    objects = ExperienceManager()


class SharedExperience(models.Model):
    class Meta:
        app_label = 'shoutit'
        unique_together = ('Experience', 'OwnerUser',)

    Experience = models.ForeignKey(Experience, related_name='SharedExperiences')
    OwnerUser = models.ForeignKey(User, related_name='SharedExperiences')
    DateCreated = models.DateTimeField(auto_now_add=True)


class Comment(models.Model):
    class Meta:
        app_label = 'shoutit'

    def __unicode__(self):
        return unicode(self.id) + ": " + unicode(self.Text)

    AboutPost = models.ForeignKey(Post, related_name='Comments', null=True)
    OwnerUser = models.ForeignKey(User, related_name='+')
    IsDisabled = models.BooleanField(default=False)
    Text = models.TextField(max_length=300)
    DateCreated = models.DateTimeField(auto_now_add=True)


class GalleryItem(models.Model):
    class Meta:
        app_label = 'shoutit'
        unique_together = ('Item', 'Gallery',)

    Item = models.ForeignKey(Item, related_name='+')
    Gallery = models.ForeignKey('Gallery', related_name='GalleryItems')
    IsDisable = models.BooleanField(default=False)
    IsMuted = models.BooleanField(default=False)
    DateCreated = models.DateTimeField(auto_now_add=True)


class Gallery(models.Model):
    class Meta:
        app_label = 'shoutit'

    def __unicode__(self):
        return unicode(self.id) + ": " + unicode(self.Description)

    Description = models.TextField(max_length=500, default='')
    OwnerBusiness = models.ForeignKey(BusinessProfile, related_name='Galleries')
    Category = models.OneToOneField(Category, related_name='+', null=True)


class PaymentsManager(models.Manager):
    def GetUserPayments(self, user):
        if isinstance(user, User):
            return self.filter(User=user)
        elif isinstance(user, basestring):
            return self.filter(User__username__iexact=user)
        elif isinstance(user, UserProfile):
            return self.filter(User__pk=user.User_id)
        elif isinstance(user, BusinessProfile):
            return self.filter(User__pk=user.User_id)
        elif isinstance(user, int):
            return self.filter(User__pk=user)

    def GetObjectPayments(self, object):
        return self.filter(content_type=ContentType.objects.get_for_model(object.__class__), object_pk=object.pk)


class Payment(models.Model):
    class Meta:
        app_label = 'shoutit'

    User = models.ForeignKey(User, related_name='Payments')
    DateCreated = models.DateTimeField(auto_now_add=True)
    DateUpdated = models.DateTimeField(auto_now=True)
    Amount = models.FloatField()
    Currency = models.ForeignKey(Currency, related_name='+')
    Status = models.IntegerField()
    Transaction = models.ForeignKey('Transaction', related_name='Payment')

    content_type = models.ForeignKey(ContentType, null=True)
    object_pk = models.TextField(null=True)
    Object = generic.GenericForeignKey(fk_field='object_pk')

    objects = PaymentsManager()


class Transaction(models.Model):
    class Meta:
        app_label = 'shoutit'

    RemoteIdentifier = models.CharField(max_length=1024)
    RemoteData = models.CharField(max_length=1024)
    RemoteStatus = models.CharField(max_length=1024)
    DateCreated = models.DateTimeField(auto_now_add=True)
    DateUpdated = models.DateTimeField(auto_now=True)


class Voucher(models.Model):
    class Meta:
        app_label = 'shoutit'

    DealBuy = models.ForeignKey(DealBuy, related_name='Vouchers')
    Code = models.CharField(max_length=22)
    DateGenerated = models.DateTimeField(auto_now_add=True)
    IsValidated = models.BooleanField(default=False)
    IsSent = models.BooleanField(default=False)


class Event(Post):
    class Meta:
        app_label = 'shoutit'

    def __unicode__(self):
        return unicode(self.id)

    EventType = models.IntegerField(default=0)
    objects = EventManager()

    content_type = models.ForeignKey(ContentType, null=True)
    object_pk = models.TextField(null=True)
    AttachedObject = generic.GenericForeignKey(fk_field='object_pk')


class Report(models.Model):
    class Meta:
        app_label = 'shoutit'

    def __unicode__(self):
        return 'From : ' + self.Type()

    User = models.ForeignKey(User, related_name='Reports')
    Text = models.TextField(default='', max_length=300)
    Type = models.IntegerField(default=0)
    IsSolved = models.BooleanField(default=False)
    IsDisabled = models.BooleanField(default=False)
    DateCreated = models.DateTimeField(auto_now_add=True)

    content_type = models.ForeignKey(ContentType, null=True)
    object_pk = models.TextField(null=True)
    AttachedObject = generic.GenericForeignKey(fk_field='object_pk')

    @property
    def Type(self):
        return ReportType.values[self.Type]


class Service(models.Model):
    class Meta:
        app_label = 'shoutit'

    Code = models.CharField(max_length=256)
    Name = models.CharField(max_length=1024)
    Price = models.FloatField()


class ServiceManager(models.Manager):
    def GetUserServiceBuyRemaining(self, user, service_code):
        return self.values(ServiceBuy._meta.get_field_by_name('User')[0].column).filter(User=user,
                                                                                        Service__Code__iexact=service_code).annotate(
            buys_count=Sum('Amount')).extra(select={
            'used_count': 'SELECT SUM("%(table)s"."%(amount)s") FROM "%(table)s" WHERE "%(table)s"."%(user_id)s" = %(uid)d AND "%(table)s"."%(service_id)s" IN (%(sid)s)' % {
                'table': ServiceUsage._meta.db_table,
                'user_id': ServiceUsage._meta.get_field_by_name('User')[0].column,
                'uid': user.pk,
                'service_id': ServiceUsage._meta.get_field_by_name('Service')[0].column,
                'sid': """SELECT "%(table)s"."id" FROM "%(table)s" WHERE "%(table)s"."%(code)s" = '%(service_code)s'""" % {
                    'table': Service._meta.db_table,
                    'code': Service._meta.get_field_by_name('Code')[0].column,
                    'service_code': service_code
                },
                'amount': ServiceUsage._meta.get_field_by_name('Amount')[0].column,
            }
        }).values('used_count', 'buys_count')


class ServiceBuy(models.Model):
    class Meta:
        app_label = 'shoutit'

    User = models.ForeignKey(User, related_name='Services')
    Service = models.ForeignKey('Service', related_name='Buyers')
    Amount = models.IntegerField(default=1)
    DateBought = models.DateTimeField(auto_now_add=True)

    objects = ServiceManager()


class ServiceUsage(models.Model):
    class Meta:
        app_label = 'shoutit'

    User = models.ForeignKey(User, related_name='ServicesUsages')
    Service = models.ForeignKey('Service', related_name='BuyersUsages')
    Amount = models.IntegerField(default=1)
    DateUsed = models.DateTimeField(auto_now_add=True)


class Subscription(models.Model):
    class Meta:
        app_label = 'shoutit'

    #Id = models.CharField(max_length=19)
    Type = models.IntegerField(default=0)
    State = models.IntegerField(default=0)
    SignUpDate = models.DateTimeField(null=True)
    DeactivateDate = models.DateTimeField(null=True)
    UserName = models.CharField(max_length=64)
    Password = models.CharField(max_length=24)


#PAUSE: PAYPAL

#from paypal.standard.ipn.signals import payment_was_successful, payment_was_flagged,subscription_signup,subscription_cancel
#from paypal.standard.pdt.views import pdt
#import re
#
#def paypal_payment_flag(sender, **kwargs):
#	import apps.shoutit.controllers.payment_controller
#	#('Active', 'Cancelled', 'Cleared', 'Completed', 'Denied', 'Paid', 'Pending', 'Processed', 'Refused', 'Reversed', 'Rewarded', 'Unclaimed', 'Uncleared')
#	ipn_obj = sender
#	regex = re.compile(r'(\w+)_(\w+)_User_([^_]+)(?:_x_(\d+))?')
#	match = regex.match(ipn_obj.invoice)
#	transaction_data = 'PayPal TXN %s#%s by %s (%s)' % (ipn_obj.txn_type, ipn_obj.txn_id, ipn_obj.payer_id, ipn_obj.payer_email)
#	transaction_identifier = 'PayPal#%s' % ipn_obj.txn_id
#	if match:
#		item_type, item_id, user_id, amount = match.groups()
#		if ipn_obj.payment_status in ['Completed', 'Paid']:
#			if item_type == 'Deal':
#				apps.shoutit.controllers.payment_controller.PayForDeal(int(user_id), item_id, amount, transaction_data, transaction_identifier)
#			elif item_type == 'Service':
#				apps.shoutit.controllers.payment_controller.PayForService(int(user_id), item_id, amount, transaction_data, transaction_identifier)
#		elif ipn_obj.payment_status in ['Cancelled', 'Reversed', 'Refunded']:
#			transaction_identifier = 'PayPal#%s' % ipn_obj.parent_txn_id
#			if item_type == 'Deal':
#				apps.shoutit.controllers.payment_controller.CancelPaymentForDeal(int(user_id), item_id, transaction_data, transaction_identifier)
#			elif item_type == 'Service':
#				apps.shoutit.controllers.payment_controller.CancelPaymentForService(int(user_id), item_id, transaction_data, transaction_identifier)

#payment_was_successful.connect(paypal_payment_flag)
#payment_was_flagged.connect(paypal_payment_flag)

# taken own payments for now
#def business_subscribed(sender, **kwargs):
#	user = kwargs['user']
#	application = user.BusinessCreateApplication.all()[0]
#	application.Status = BUSINESS_CONFIRMATION_STATUS_WAITING_CONFIRMATION
#	application.save()
#
#def business_unsubscribed(sender, **kwargs):
#	user = kwargs['user']
#	application = user.BusinessCreateApplication.all()[0]
#	application.Status = BUSINESS_CONFIRMATION_STATUS_WAITING_PAYMENT
#	application.save()
#
#subscribed.connect(business_subscribed)
#unsubscribed.connect(business_unsubscribed)


class PredefinedCity(models.Model):
    class Meta:
        app_label = 'shoutit'

    def __unicode__(self):
        return unicode(self.Country + ':' + self.City)

    City = models.CharField(max_length=200, default='', db_index=True, unique=True)
    EncodedCity = models.CharField(max_length=200, default='', db_index=True, unique=True)
    Country = models.CharField(max_length=2, default='', db_index=True)
    Latitude = models.FloatField(default=0.0)
    Longitude = models.FloatField(default=0.0)
    Approved = models.BooleanField(default=False)
