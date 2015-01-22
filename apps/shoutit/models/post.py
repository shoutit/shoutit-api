from datetime import timedelta, datetime

from django.db import models
from django.db.models import Q, Sum
from django.conf import settings

from common.constants import POST_TYPE_DEAL, POST_TYPE_OFFER, POST_TYPE_REQUEST, POST_TYPE_EXPERIENCE, POST_TYPE_EVENT, PostType
from apps.shoutit.models.base import UUIDModel, AttachedObjectMixin
from apps.shoutit.models.item import Item
from apps.shoutit.models.stream import Stream
from apps.shoutit.models.tag import Tag
from apps.shoutit.models.business import Business

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
    class Meta:
        app_label = 'shoutit'

    objects = PostManager()

    OwnerUser = models.ForeignKey(AUTH_USER_MODEL, related_name='Posts')
    Streams = models.ManyToManyField(Stream, related_name='Posts')  # todo: move to stream as posts

    Text = models.TextField(max_length=2000, default='', db_index=True)
    Type = models.IntegerField(default=POST_TYPE_REQUEST.value, db_index=True, choices=PostType.choices)
    DatePublished = models.DateTimeField(auto_now_add=True, db_index=True)

    IsMuted = models.BooleanField(default=False, db_index=True)
    IsDisabled = models.BooleanField(default=False, db_index=True)

    Latitude = models.FloatField(default=0.0)
    Longitude = models.FloatField(default=0.0)
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

    def set_tags(self, tags):
        self.tags = tags

    def get_tags(self):
        if hasattr(self, 'tags'):
            return self.tags
        else:
            self.tags = list(self.Tags.all().select_related(depth=2))
            return self.tags

    def get_images(self):
        if not hasattr(self, '_images'):
            if self.Type == POST_TYPE_EXPERIENCE:
                self._images = list(self.Images.all().order_by('Image'))
            else:
                self._images = self.Item.get_images()
        return self._images

    def get_first_image(self):
        return self.Item.get_first_image()

    def set_images(self, images):
        images = sorted(images, key=lambda img: img.Image)
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

    def is_expired(self):
        now = datetime.now()
        if (not self.ExpiryDate and now > self.DatePublished + timedelta(days=int(settings.MAX_EXPIRY_DAYS))) or (
            self.ExpiryDate and now > self.ExpiryDate):
            return True

    def __unicode__(self):
        return unicode(self.pk) + ": " + self.get_text()


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


# todo: use attached object mixin
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


# todo: use attached object mixin
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

