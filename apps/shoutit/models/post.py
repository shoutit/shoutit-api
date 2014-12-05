from datetime import timedelta, datetime

from django.db import models
from django.db.models import Q, Sum
from django.conf import settings

from common.constants import POST_TYPE_DEAL, POST_TYPE_SELL, POST_TYPE_BUY, POST_TYPE_EXPERIENCE, POST_TYPE_EVENT
from apps.shoutit.models.base import UUIDModel, AttachedObjectMixin
from apps.shoutit.models.item import Item
from apps.shoutit.models.stream import Stream
from apps.shoutit.models.tag import Tag
from apps.shoutit.models.business import Business

AUTH_USER_MODEL = getattr(settings, 'AUTH_USER_MODEL')


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
        if not types:
            types = [POST_TYPE_SELL, POST_TYPE_BUY, POST_TYPE_DEAL]
        types = [shout_type for shout_type in types if shout_type in [POST_TYPE_SELL, POST_TYPE_BUY, POST_TYPE_DEAL]]
        shout_qs = PostManager.GetValidPosts(self, types, country_code=country_code, province_code=province_code, get_muted=get_muted,
                                             get_expired=get_expired)
        if not get_expired:
            shout_qs = self.filter_shout_expired(shout_qs)
        return shout_qs


class TradeManager(ShoutManager):
    def GetValidTrades(self, types=[], country_code=None, province_code=None, get_expired=False, get_muted=False):
        if not types:
            types = [POST_TYPE_SELL, POST_TYPE_BUY]
        types = [trade_type for trade_type in types if trade_type in [POST_TYPE_SELL, POST_TYPE_BUY]]
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


class Post(UUIDModel):
    class Meta:
        app_label = 'shoutit'

    objects = PostManager()

    OwnerUser = models.ForeignKey(AUTH_USER_MODEL, related_name='Posts')
    Streams = models.ManyToManyField(Stream, related_name='Posts')  # todo: move to stream as posts

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

    Tags = models.ManyToManyField(Tag, related_name='Shouts')
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
        return unicode(self.pk) + ": " + self.GetText()


class ShoutWrap(UUIDModel):
    class Meta:
        app_label = 'shoutit'

    def __unicode__(self):
        return unicode(self.pk) + ": " + unicode(self.Shout) + " # " + unicode(self.Rank)

    Shout = models.ForeignKey('Shout', related_name='ShoutWraps')
    Stream = models.ForeignKey(Stream, related_name='ShoutWraps')
    Rank = models.FloatField(default=1.0)


class Trade(Shout):
    class Meta:
        app_label = 'shoutit'

    def __unicode__(self):
        return unicode(self.pk) + ": " + unicode(self.Item)

    Item = models.OneToOneField('Item', related_name='Shout', db_index=True, null=True)
    RelatedStream = models.OneToOneField(Stream, related_name='InitShoutRelated', null=True)
    RecommendedStream = models.OneToOneField(Stream, related_name='InitShoutRecommended', null=True)

    StreamsCode = models.CharField(max_length=2000, default='')
    MaxFollowings = models.IntegerField(default=6)
    MaxDistance = models.FloatField(default=180.0)
    MaxPrice = models.FloatField(default=1.0)
    IsShowMobile = models.BooleanField(default=True)
    IsSSS = models.BooleanField(default=False)
    BaseDatePublished = models.DateTimeField(auto_now_add=True)
    RenewalCount = models.IntegerField(default=0)
    objects = TradeManager()


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


class Experience(Post):
    class Meta:
        app_label = 'shoutit'

    def __unicode__(self):
        return unicode(self.pk)

    AboutBusiness = models.ForeignKey(Business, related_name='Experiences')
    State = models.IntegerField(null=False)
    objects = ExperienceManager()


class SharedExperience(UUIDModel):
    class Meta:
        app_label = 'shoutit'
        unique_together = ('Experience', 'OwnerUser',)

    Experience = models.ForeignKey(Experience, related_name='SharedExperiences')
    OwnerUser = models.ForeignKey(AUTH_USER_MODEL, related_name='SharedExperiences')
    DateCreated = models.DateTimeField(auto_now_add=True)


class Video(UUIDModel):
    class Meta:
        app_label = 'shoutit'

    def __unicode__(self):
        return unicode(self.pk) + ": " + self.id_on_provider + " @ " + unicode(self.provider) + " for: " + unicode(self.item)

    shout = models.ForeignKey(Shout, related_name='videos', null=True)
    item = models.ForeignKey(Item, related_name='videos', null=True)

    url = models.URLField(max_length=1024)
    thumbnail_url = models.URLField(max_length=1024)
    provider = models.CharField(max_length=1024)
    id_on_provider = models.CharField(max_length=256)
    duration = models.IntegerField(default=0)


class StoredImage(UUIDModel):
    class Meta:
        app_label = 'shoutit'

    def __unicode__(self):
        return unicode(self.pk) + ": " + self.Image + " @ " + unicode(self.Item)

    Shout = models.ForeignKey('Shout', related_name='Images', null=True)
    Item = models.ForeignKey('Item', related_name='Images', null=True)
    Image = models.URLField(max_length=1024)


class Comment(UUIDModel):
    class Meta:
        app_label = 'shoutit'

    def __unicode__(self):
        return unicode(self.pk) + ": " + unicode(self.Text)

    AboutPost = models.ForeignKey(Post, related_name='Comments', null=True)
    OwnerUser = models.ForeignKey(AUTH_USER_MODEL, related_name='+')
    IsDisabled = models.BooleanField(default=False)
    Text = models.TextField(max_length=300)
    DateCreated = models.DateTimeField(auto_now_add=True)


class Event(Post, AttachedObjectMixin):
    class Meta:
        app_label = 'shoutit'

    def __unicode__(self):
        return unicode(self.pk)

    EventType = models.IntegerField(default=0)
    objects = EventManager()

