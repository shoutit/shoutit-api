from datetime import timedelta, datetime

from django.db import models
from django.db.models import Q, Sum
from django.conf import settings

from common.constants import POST_TYPE_DEAL, POST_TYPE_OFFER, POST_TYPE_REQUEST, POST_TYPE_EXPERIENCE, POST_TYPE_EVENT, PostType, EventType
from shoutit.models.base import UUIDModel, AttachedObjectMixin

AUTH_USER_MODEL = getattr(settings, 'AUTH_USER_MODEL')


class PostManager(models.Manager):
    def get_valid_posts(self, types=None, country=None, city=None, get_expired=False, get_muted=False):

        qs = self
        qs = qs.distinct().filter(IsDisabled=False)

        if types:
            qs = qs.filter(Type__in=types)

        if country:
            qs = qs.filter(CountryCode__iexact=country)

        if city:
            qs = qs.filter(ProvinceCode__iexact=city)

        if not get_muted:
            qs = qs.filter(IsMuted=False)

        if not get_expired:
            qs = self.filter_expired_out(qs)

        return qs

    def filter_expired_out(self, qs):
        today = datetime.today()
        days = timedelta(days=int(settings.MAX_EXPIRY_DAYS))
        day = today - days
        return qs.filter(
            Q(Type=POST_TYPE_EXPERIENCE) | Q(Type=POST_TYPE_EVENT)
            | (
                (Q(Type=POST_TYPE_REQUEST) | Q(Type=POST_TYPE_OFFER))
                & (
                    Q(shout__ExpiryDate__isnull=True, DatePublished__range=(day, today))
                    |
                    Q(shout__ExpiryDate__isnull=False, shout__ExpiryDate__gte=today)
                )
            )
        )


class ShoutManager(PostManager):
    def get_valid_shouts(self, types=None, country=None, city=None, get_expired=False, get_muted=False):
        if not types:
            types = [POST_TYPE_OFFER, POST_TYPE_REQUEST, POST_TYPE_DEAL]
        types = list(set(types).intersection([POST_TYPE_OFFER, POST_TYPE_REQUEST, POST_TYPE_DEAL]))
        return PostManager.get_valid_posts(self, types, country=country, city=city, get_expired=get_expired, get_muted=get_muted)

    def filter_expired_out(self, qs):
        today = datetime.today()
        days = timedelta(days=int(settings.MAX_EXPIRY_DAYS))
        day = today - days
        return qs.filter(Q(ExpiryDate__isnull=True, DatePublished__range=(day, today)) | Q(ExpiryDate__isnull=False, ExpiryDate__gte=today))


class TradeManager(ShoutManager):
    def get_valid_trades(self, types=None, country=None, city=None, get_expired=False, get_muted=False):
        if not types:
            types = [POST_TYPE_OFFER, POST_TYPE_REQUEST]
        types = list(set(types).intersection([POST_TYPE_OFFER, POST_TYPE_REQUEST]))
        return ShoutManager.get_valid_shouts(self, types=types, country=country, city=city, get_expired=get_expired, get_muted=get_muted)

    def get_valid_requests(self, country=None, city=None, get_expired=False, get_muted=False):
        types = [POST_TYPE_REQUEST]
        return self.get_valid_trades(types=types, country=country, city=city, get_expired=get_expired, get_muted=get_muted)

    def get_valid_offers(self, country=None, city=None, get_expired=False, get_muted=False):
        types = [POST_TYPE_OFFER]
        return self.get_valid_trades(types=types, country=country, city=city, get_expired=get_expired, get_muted=get_muted)


class DealManager(ShoutManager):
    def get_valid_deals(self, country=None, city=None, get_expired=False, get_muted=False):
        return ShoutManager.get_valid_shouts(self, [POST_TYPE_DEAL], country=country, city=city, get_expired=get_expired, get_muted=get_muted)


class ExperienceManager(PostManager):
    def get_valid_experiences(self, country=None, city=None, get_muted=False):
        return PostManager.get_valid_posts(self, types=[POST_TYPE_EXPERIENCE], country=country, city=city, get_expired=True, get_muted=get_muted)


class EventManager(PostManager):
    def get_valid_events(self, country=None, city=None, get_muted=False):
        return PostManager.get_valid_posts(self, types=[POST_TYPE_EVENT], country=country, city=city, get_expired=True, get_muted=get_muted)


class Post(UUIDModel):
    OwnerUser = models.ForeignKey(AUTH_USER_MODEL, related_name='Posts')
    Streams = models.ManyToManyField('shoutit.Stream', related_name='Posts')  # todo: move to stream as posts

    Text = models.TextField(max_length=2000, default='', db_index=True, blank=True)
    Type = models.IntegerField(default=POST_TYPE_REQUEST.value, db_index=True, choices=PostType.choices)
    DatePublished = models.DateTimeField(auto_now_add=True, db_index=True)

    IsMuted = models.BooleanField(default=False, db_index=True)
    IsDisabled = models.BooleanField(default=False, db_index=True)

    Latitude = models.FloatField(default=0.0)
    Longitude = models.FloatField(default=0.0)
    CountryCode = models.CharField(max_length=2, db_index=True, null=True, blank=True)
    ProvinceCode = models.CharField(max_length=200, db_index=True, null=True, blank=True)
    Address = models.CharField(max_length=200, db_index=True, null=True, blank=True)

    objects = PostManager()

    def Mute(self):
        self.IsMuted = True
        self.save()


class Shout(Post):
    Tags = models.ManyToManyField('shoutit.Tag', related_name='Shouts')
    ExpiryDate = models.DateTimeField(null=True, blank=True, default=None, db_index=True)
    ExpiryNotified = models.BooleanField(default=False)

    objects = ShoutManager()

    def __unicode__(self):
        return unicode(self.pk) + ": " + self.get_text()

    def set_tags(self, tags):
        self.tags = tags

    def get_tags(self):
        if hasattr(self, 'tags'):
            return self.tags
        else:
            self.tags = list(self.Tags.all().select_related())
            return self.tags

    def get_images(self):
        if not hasattr(self, '_images'):
            if self.Type == POST_TYPE_EXPERIENCE:
                self._images = list(self.Images.all().order_by('image'))
            else:
                self._images = self.Item.get_images()
        return self._images

    def get_first_image(self):
        return self.Item.get_first_image()

    def set_images(self, images):
        images = sorted(images, key=lambda img: img.image)
        self._images = images
        if hasattr(self, 'Item'):
            self.Item.set_images(images)

    def get_videos(self):
        if not hasattr(self, '_videos'):
            if self.Type == POST_TYPE_EXPERIENCE:
                self._videos = list(self.videos.all())
            else:
                self._videos = self.Item.get_videos()
        return self._videos

    def set_videos(self, videos):
        self._videos = videos
        if hasattr(self, 'Item'):
            self.Item.set_videos(videos)

    def get_first_video(self):
        return self.Item.get_first_video()

    def get_text(self):
        text = ''
        if self.Type == POST_TYPE_REQUEST or self.Type == POST_TYPE_OFFER:
            try:
                text = self.trade.Item.Name + ' ' + self.Text
            except Exception, e:
                print e
        else:
            text = self.Text

        return text

    @property
    def is_expired(self):
        now = datetime.now()
        if (not self.ExpiryDate and now > self.DatePublished + timedelta(days=int(settings.MAX_EXPIRY_DAYS))) or (
            self.ExpiryDate and now > self.ExpiryDate):
            return True


class ShoutWrap(UUIDModel):
    Shout = models.ForeignKey('shoutit.Shout', related_name='ShoutWraps')
    Stream = models.ForeignKey('shoutit.Stream', related_name='ShoutWraps')
    Rank = models.FloatField(default=1.0)

    def __unicode__(self):
        return unicode(self.pk) + ": " + unicode(self.Shout) + " # " + unicode(self.Rank)


class Trade(Shout):
    Item = models.OneToOneField('shoutit.Item', related_name='Shout', db_index=True, null=True, blank=True)
    RelatedStream = models.OneToOneField('shoutit.Stream', related_name='InitShoutRelated', null=True, blank=True)
    RecommendedStream = models.OneToOneField('shoutit.Stream', related_name='InitShoutRecommended', null=True, blank=True)

    StreamsCode = models.CharField(max_length=2000, default='', blank=True)
    MaxFollowings = models.IntegerField(default=6)
    MaxDistance = models.FloatField(default=180.0)
    MaxPrice = models.FloatField(default=1.0)
    IsShowMobile = models.BooleanField(default=True)
    IsSSS = models.BooleanField(default=False)
    BaseDatePublished = models.DateTimeField(auto_now_add=True)
    RenewalCount = models.IntegerField(default=0)

    objects = TradeManager()

    def __unicode__(self):
        return unicode(self.pk) + ": " + unicode(self.Item)


class Deal(Shout):
    MinBuyers = models.IntegerField(default=0)
    MaxBuyers = models.IntegerField(null=True, blank=True)
    OriginalPrice = models.FloatField()
    IsClosed = models.BooleanField(default=False)
    Item = models.ForeignKey('shoutit.Item', related_name='Deals', on_delete=models.SET_NULL, null=True, blank=True)
    ValidFrom = models.DateTimeField(null=True, blank=True)
    ValidTo = models.DateTimeField(null=True, blank=True)

    objects = DealManager()

    def BuyersCount(self):
        return self.Buys.aggregate(buys=Sum('Amount'))['buys']

    def AvailableCount(self):
        return self.MaxBuyers - self.BuyersCount()


class Experience(Post):
    AboutBusiness = models.ForeignKey('shoutit.Business', related_name='Experiences')
    State = models.IntegerField(null=False)

    objects = ExperienceManager()

    def __unicode__(self):
        return unicode(self.pk)


class SharedExperience(UUIDModel):
    Experience = models.ForeignKey('shoutit.Experience', related_name='SharedExperiences')
    OwnerUser = models.ForeignKey(AUTH_USER_MODEL, related_name='SharedExperiences')
    DateCreated = models.DateTimeField(auto_now_add=True)

    class Meta(UUIDModel.Meta):
        unique_together = ('Experience', 'OwnerUser',)


# todo: use attached object mixin
class Video(UUIDModel):
    shout = models.ForeignKey('shoutit.Shout', related_name='videos', null=True, blank=True)
    item = models.ForeignKey('shoutit.Item', related_name='videos', null=True, blank=True)

    url = models.URLField(max_length=1024)
    thumbnail_url = models.URLField(max_length=1024)
    provider = models.CharField(max_length=1024)
    id_on_provider = models.CharField(max_length=256)
    duration = models.IntegerField(default=0)

    def __unicode__(self):
        return unicode(self.pk) + ": " + self.id_on_provider + " @ " + unicode(self.provider) + " for: " + unicode(self.item)


# todo: use attached object mixin
class StoredImage(UUIDModel):
    Shout = models.ForeignKey('shoutit.Shout', related_name='Images', null=True, blank=True)
    Item = models.ForeignKey('shoutit.Item', related_name='Images', null=True, blank=True)
    image = models.CharField(max_length=1024)

    def __unicode__(self):
        return unicode(self.pk) + ": " + self.image + " @ " + unicode(self.Item)


class Comment(UUIDModel):
    AboutPost = models.ForeignKey('shoutit.Post', related_name='Comments', null=True, blank=True)
    OwnerUser = models.ForeignKey(AUTH_USER_MODEL, related_name='+')
    IsDisabled = models.BooleanField(default=False)
    Text = models.TextField(max_length=300)
    DateCreated = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return unicode(self.pk) + ": " + unicode(self.Text)


class Event(Post, AttachedObjectMixin):
    EventType = models.IntegerField(default=0, choices=EventType.choices)

    objects = EventManager()

    def __unicode__(self):
        return unicode(EventType.values[self.EventType])
