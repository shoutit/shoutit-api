from __future__ import unicode_literals
from datetime import timedelta, datetime
import time
import json

from django.db import models
from django.db.models import Q, Sum, F
from django.conf import settings

from common.constants import POST_TYPE_DEAL, POST_TYPE_OFFER, POST_TYPE_REQUEST, POST_TYPE_EXPERIENCE, POST_TYPE_EVENT, PostType, EventType, \
    TAGS_PER_POST
from shoutit.models.base import UUIDModel, AttachedObjectMixin, APIModelMixin

AUTH_USER_MODEL = getattr(settings, 'AUTH_USER_MODEL')


class PostManager(models.Manager):
    def get_valid_posts(self, types=None, country=None, city=None, get_expired=False, get_muted=False):

        qs = self
        qs = qs.distinct().filter(is_disabled=False)

        if types:
            qs = qs.filter(type__in=types)

        if country:
            qs = qs.filter(country__iexact=country)

        if city:
            qs = qs.filter(city__iexact=city)

        if not get_muted:
            qs = qs.filter(muted=False)

        if not get_expired:
            qs = self.filter_expired_out(qs)

        # todo: filter out posts by disabled / deactivated users
        return qs

    def filter_expired_out(self, qs):
        today = datetime.today()
        days = timedelta(days=int(settings.MAX_EXPIRY_DAYS))
        day = today - days
        return qs.filter(
            Q(type=POST_TYPE_EXPERIENCE) | Q(type=POST_TYPE_EVENT)
            | (
                (Q(type=POST_TYPE_REQUEST) | Q(type=POST_TYPE_OFFER))
                & (
                    Q(shout__expiry_date__isnull=True, date_published__range=(day, today))
                    |
                    Q(shout__expiry_date__isnull=False, shout__expiry_date__gte=today)
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
        return qs.filter(Q(expiry_date__isnull=True, date_published__range=(day, today)) | Q(expiry_date__isnull=False, expiry_date__gte=today))


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


class Post(UUIDModel, APIModelMixin):
    user = models.ForeignKey(AUTH_USER_MODEL, related_name='Posts')

    # todo: deprecate
    Streams = models.ManyToManyField('shoutit.Stream', related_name='Posts')

    # the uuid(s) of streams this post appears in. assuming uuid with hyphens size is 36 characters
    # json string that looks like: [user-uuid,tag1-uuid,tag2-uuid,...]
    streams2_ids = models.CharField(max_length=2 + 36 + (TAGS_PER_POST * 36) + TAGS_PER_POST, blank=True, default="")

    text = models.TextField(max_length=2000, default='', db_index=True, blank=True)
    type = models.IntegerField(default=POST_TYPE_REQUEST.value, db_index=True, choices=PostType.choices)
    date_published = models.DateTimeField(auto_now_add=True, db_index=True)

    muted = models.BooleanField(default=False, db_index=True)
    is_disabled = models.BooleanField(default=False, db_index=True)

    latitude = models.FloatField(default=0.0)
    longitude = models.FloatField(default=0.0)
    country = models.CharField(max_length=2, db_index=True, null=True, blank=True)
    city = models.CharField(max_length=200, db_index=True, null=True, blank=True)
    address = models.CharField(max_length=200, db_index=True, null=True, blank=True)

    objects = PostManager()

    def mute(self):
        self.muted = True
        self.save()

    @property
    def owner(self):
        return self.user

    @property
    def type_name(self):
        return PostType.values[self.type]

    @property
    def location(self):
        return {
            'country': self.country,
            'city': self.city,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'address': self.address,
        }

    @property
    def thumbnail(self):
        if self.type in [POST_TYPE_REQUEST, POST_TYPE_OFFER]:
            return self.item.thumbnail
        else:
            return None

    @property
    def video_url(self):
        if self.type in [POST_TYPE_REQUEST, POST_TYPE_OFFER]:
            return self.item.video_url
        else:
            return None

    def refresh_streams2_ids(self):
        # save the ids of streams2 this post appears in as a json array, to be used in raw queries.
        self.streams2_ids = json.dumps(self.streams2.values_list('id', flat=True))


class Shout(Post):
    tags = models.ManyToManyField('shoutit.Tag', related_name='shouts')
    expiry_date = models.DateTimeField(null=True, blank=True, default=None, db_index=True)
    expiry_notified = models.BooleanField(default=False)

    objects = ShoutManager()

    def __str__(self):
        return unicode(self.pk) + ": " + self.get_text()

    def set_tags(self, tags):
        self._tags = tags

    def get_tags(self):
        if not hasattr(self, '_tags'):
            self._tags = list(self.tags.all())
        return self._tags

    def get_images(self):
        if not hasattr(self, '_images'):
            if self.type == POST_TYPE_EXPERIENCE:
                self._images = list(self.images.all().order_by('image'))
            else:
                self._images = self.item.get_images()
        return self._images

    def get_first_image(self):
        return self.item.get_first_image()

    def set_images(self, images):
        images = sorted(images, key=lambda img: img.image)
        self._images = images
        if hasattr(self, 'item'):
            self.item.set_images(images)

    def get_videos(self):
        if not hasattr(self, '_videos'):
            if self.type == POST_TYPE_EXPERIENCE:
                self._videos = list(self.videos.all())
            else:
                self._videos = self.item.get_videos()
        return self._videos

    def set_videos(self, videos):
        self._videos = videos
        if hasattr(self, 'item'):
            self.item.set_videos(videos)

    def get_first_video(self):
        return self.item.get_first_video()

    def get_text(self):
        text = ''
        if self.type == POST_TYPE_REQUEST or self.type == POST_TYPE_OFFER:
            try:
                text = self.trade.item.name + ' ' + self.text
            except Exception, e:
                print e
        else:
            text = self.text

        return text

    @property
    def is_expired(self):
        now = datetime.now()
        if (not self.expiry_date and now > self.date_published + timedelta(days=int(settings.MAX_EXPIRY_DAYS))) or (
            self.expiry_date and now > self.expiry_date):
            return True


class ShoutWrap(UUIDModel):
    shout = models.ForeignKey('shoutit.Shout', related_name='ShoutWraps')
    Stream = models.ForeignKey('shoutit.Stream', related_name='ShoutWraps')
    rank = models.FloatField(default=1.0)

    def __str__(self):
        return unicode(self.pk) + ": " + unicode(self.shout) + " # " + unicode(self.rank)


class Trade(Shout):
    item = models.OneToOneField('shoutit.Item', related_name='shout', db_index=True, null=True, blank=True)

    related_stream = models.OneToOneField('shoutit.Stream', related_name='init_shout_related', null=True, blank=True)
    recommended_stream = models.OneToOneField('shoutit.Stream', related_name='init_shout_recommended', null=True, blank=True)

    StreamsCode = models.CharField(max_length=2000, default='', blank=True)
    MaxFollowings = models.IntegerField(default=6)
    MaxDistance = models.FloatField(default=180.0)
    MaxPrice = models.FloatField(default=1.0)

    is_sss = models.BooleanField(default=False)

    base_date_published = models.DateTimeField(auto_now_add=True)
    renewal_count = models.PositiveSmallIntegerField(default=0)

    objects = TradeManager()

    def __str__(self):
        return unicode(self.pk) + ": " + unicode(self.item)

    @property
    def related_requests(self):
        if self.type == POST_TYPE_REQUEST:
            related_requests_stream = self.related_stream
        else:
            related_requests_stream = self.recommended_stream
        return get_ranked_stream_shouts(related_requests_stream)

    @property
    def related_offers(self):
        if self.type == POST_TYPE_OFFER:
            related_offers_stream = self.related_stream
        else:
            related_offers_stream = self.recommended_stream
        return get_ranked_stream_shouts(related_offers_stream)


# todo: refactor
def get_ranked_stream_shouts(stream, limit=3):
    if not stream:
        return []

    today = datetime.today()
    days = timedelta(days=int(settings.MAX_EXPIRY_DAYS))
    begin = today - days
    base_timestamp = int(time.mktime(begin.utctimetuple()))
    now_timestamp = int(time.mktime(datetime.now().utctimetuple()))
    now_timestamp_string = str(datetime.now())

    time_axis = '(extract (epoch from age(\'%s\', "shoutit_post"."date_published"))/ %d)' % (
        now_timestamp_string, now_timestamp - base_timestamp)

    shout_wraps = stream.ShoutWraps.select_related('shout', 'shout__trade').filter(
        Q(shout__expiry_date__isnull=True, shout__date_published__range=(begin, today)) | Q(shout__expiry_date__isnull=False,
                                                                                          shout__date_published__lte=F(
                                                                                              'shout__expiry_date')),
        shout__muted=False, shout__is_disabled=False).extra(select={'overall_rank': '(("rank" * 2) + %s) / 3' % time_axis}).extra(
        order_by=['overall_rank'])[:limit]
    if not shout_wraps:
        return []
    return [shout_wrap.shout.trade for shout_wrap in shout_wraps]


class Deal(Shout):
    MinBuyers = models.IntegerField(default=0)
    MaxBuyers = models.IntegerField(null=True, blank=True)
    OriginalPrice = models.FloatField()
    IsClosed = models.BooleanField(default=False)
    item = models.ForeignKey('shoutit.Item', related_name='Deals', on_delete=models.SET_NULL, null=True, blank=True)
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

    def __str__(self):
        return unicode(self.pk)


class SharedExperience(UUIDModel):
    Experience = models.ForeignKey('shoutit.Experience', related_name='SharedExperiences')
    user = models.ForeignKey(AUTH_USER_MODEL, related_name='SharedExperiences')
    DateCreated = models.DateTimeField(auto_now_add=True)

    class Meta(UUIDModel.Meta):
        unique_together = ('Experience', 'user',)


# todo: use attached object mixin
class Video(UUIDModel):
    shout = models.ForeignKey('shoutit.Shout', related_name='videos', null=True, blank=True)
    item = models.ForeignKey('shoutit.Item', related_name='videos', null=True, blank=True)

    url = models.URLField(max_length=1024)
    thumbnail_url = models.URLField(max_length=1024)
    provider = models.CharField(max_length=1024)
    id_on_provider = models.CharField(max_length=256)
    duration = models.IntegerField()

    def __str__(self):
        return unicode(self.pk) + ": " + self.id_on_provider + " @ " + unicode(self.provider) + " for: " + unicode(self.item)


# todo: use attached object mixin
class StoredImage(UUIDModel):
    shout = models.ForeignKey('shoutit.Shout', related_name='images', null=True, blank=True)
    item = models.ForeignKey('shoutit.Item', related_name='images', null=True, blank=True)
    image = models.CharField(max_length=1024)

    def __str__(self):
        return unicode(self.image)


class Comment(UUIDModel):
    AboutPost = models.ForeignKey('shoutit.Post', related_name='Comments', null=True, blank=True)
    user = models.ForeignKey(AUTH_USER_MODEL, related_name='+')
    is_disabled = models.BooleanField(default=False)
    text = models.TextField(max_length=300)
    DateCreated = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return unicode(self.pk) + ": " + unicode(self.text)


class Event(Post, AttachedObjectMixin):
    EventType = models.IntegerField(default=0, choices=EventType.choices)

    objects = EventManager()

    def __str__(self):
        return unicode(EventType.values[self.EventType])
