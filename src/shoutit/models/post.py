from __future__ import unicode_literals
from datetime import timedelta, datetime
from django.contrib.contenttypes.fields import GenericRelation
from django.contrib.postgres.fields import ArrayField
from django.utils import timezone
from django.db import models
from django.db.models import Q
from django.conf import settings
from elasticsearch import RequestError
from elasticsearch_dsl import DocType, String, Date, Double, Integer, Boolean

from common.constants import (POST_TYPE_DEAL, POST_TYPE_OFFER, POST_TYPE_REQUEST,
    POST_TYPE_EXPERIENCE, POST_TYPE_EVENT, PostType, EventType, COUNTRY_ISO)
from common.utils import date_unix
from shoutit.models import Tag
from shoutit.models.base import UUIDModel, AttachedObjectMixin, APIModelMixin, LocationMixin

AUTH_USER_MODEL = getattr(settings, 'AUTH_USER_MODEL')


class PostManager(models.Manager):
    def get_valid_posts(self, types=None, country=None, city=None, get_expired=False,
                        get_muted=False):

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
    def get_valid_shouts(self, types=None, country=None, city=None, get_expired=False,
                         get_muted=False):
        if not types:
            types = [POST_TYPE_OFFER, POST_TYPE_REQUEST, POST_TYPE_DEAL]
        types = list(set(types).intersection([POST_TYPE_OFFER, POST_TYPE_REQUEST, POST_TYPE_DEAL]))
        return PostManager.get_valid_posts(self, types, country=country, city=city,
                                           get_expired=get_expired, get_muted=get_muted)

    def filter_expired_out(self, qs):
        today = datetime.today()
        days = timedelta(days=int(settings.MAX_EXPIRY_DAYS))
        day = today - days
        return qs.filter(Q(expiry_date__isnull=True, date_published__range=(day, today)) | Q(
            expiry_date__isnull=False, expiry_date__gte=today))

    def get_valid_requests(self, country=None, city=None, get_expired=False, get_muted=False):
        types = [POST_TYPE_REQUEST]
        return self.get_valid_shouts(types=types, country=country, city=city,
                                     get_expired=get_expired, get_muted=get_muted)

    def get_valid_offers(self, country=None, city=None, get_expired=False, get_muted=False):
        types = [POST_TYPE_OFFER]
        return self.get_valid_shouts(types=types, country=country, city=city,
                                     get_expired=get_expired, get_muted=get_muted)


class EventManager(PostManager):
    def get_valid_events(self, country=None, city=None, get_muted=False):
        return PostManager.get_valid_posts(self, types=[POST_TYPE_EVENT], country=country,
                                           city=city, get_expired=True, get_muted=get_muted)


class Post(UUIDModel, APIModelMixin, LocationMixin):
    user = models.ForeignKey(AUTH_USER_MODEL, related_name='posts')
    text = models.TextField(max_length=1000, blank=True)
    type = models.IntegerField(default=POST_TYPE_REQUEST.value, db_index=True,
                               choices=PostType.choices)
    date_published = models.DateTimeField(default=timezone.now, db_index=True)

    muted = models.BooleanField(default=False, db_index=True)
    is_disabled = models.BooleanField(default=False, db_index=True)

    priority = models.SmallIntegerField(default=0)
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
    def date_published_unix(self):
        return date_unix(self.date_published)

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


class Shout(Post):
    tags = ArrayField(Tag._meta.get_field('name'))
    category = models.ForeignKey('shoutit.Category', related_name='shouts', null=True)

    item = models.OneToOneField('shoutit.Item', related_name='%(class)s', db_index=True, null=True,
                                blank=True)
    renewal_count = models.PositiveSmallIntegerField(default=0)

    expiry_date = models.DateTimeField(null=True, blank=True, default=None, db_index=True)
    expiry_notified = models.BooleanField(default=False)

    is_sss = models.BooleanField(default=False)

    conversations = GenericRelation('shoutit.Conversation', related_query_name='shout')

    objects = ShoutManager()

    def __unicode__(self):
        return unicode(self.pk) + ": " + unicode(self.item)

    @property
    def images(self):
        return self.item.images

    @property
    def videos(self):
        return self.item.videos.all()

    @property
    def tag_objects(self):
        return Tag.objects.filter(name__in=self.tags)

    def get_text(self):
        text = ''
        if self.type == POST_TYPE_REQUEST or self.type == POST_TYPE_OFFER:
            try:
                text = self.shout.item.name + ' ' + self.text
            except Exception, e:
                print e
        else:
            text = self.text

        return text

    @property
    def is_expired(self):
        now = datetime.now()
        if (not self.expiry_date and now > self.date_published + timedelta(
                days=int(settings.MAX_EXPIRY_DAYS))) or (
                    self.expiry_date and now > self.expiry_date):
            return True

    @property
    def related_requests(self):
        if self.type == POST_TYPE_REQUEST:
            return []
        else:
            return []

    @property
    def related_offers(self):
        if self.type == POST_TYPE_OFFER:
            return []
        else:
            return []

    @property
    def track_properties(self):
        return {
            'type': self.type_name,
            'category': self.category.name,
            'Country': COUNTRY_ISO.get(self.country),
            'Region': self.state,
            'City': self.city,
            'images': len(self.images),
            'videos': self.videos.count(),
            'price': self.item.price,
            'currency': self.item.currency.name,
            'shout_id': self.pk
        }


class ShoutIndex(DocType):
    # indexed
    type = String(index='not_analyzed')
    title = String(analyzer='snowball', fields={'raw': String(index='not_analyzed')})
    text = String(analyzer='snowball')
    tags_count = Integer()
    tags = String(index='not_analyzed')
    category = String(index='not_analyzed')
    country = String(index='not_analyzed')
    postal_code = String(index='not_analyzed')
    state = String(index='not_analyzed')
    city = String(index='not_analyzed')
    latitude = Double()
    longitude = Double()
    price = Double()
    uid = String(index='not_analyzed')
    username = String(index='not_analyzed')
    date_published = Date()

    # todo: should not be analysed or indexed
    currency = String(index='not_analyzed')
    address = String(index='not_analyzed')
    thumbnail = String(index='not_analyzed')
    video_url = String(index='not_analyzed')

    is_sss = Boolean()
    priority = Integer()

    class Meta:
        index = settings.ENV

    @property
    def date_published_unix(self):
        return date_unix(self.date_published)

# initiate the index if not initiated
try:
    ShoutIndex.init()
except RequestError:
    pass


class Event(Post, AttachedObjectMixin):
    event_type = models.IntegerField(default=0, choices=EventType.choices)

    objects = EventManager()

    def __unicode__(self):
        return unicode(EventType.values[self.event_type])


class Video(UUIDModel):
    url = models.URLField(max_length=1024)
    thumbnail_url = models.URLField(max_length=1024)
    provider = models.CharField(max_length=1024)
    id_on_provider = models.CharField(max_length=256)
    duration = models.PositiveIntegerField()

    def __unicode__(self):
        return unicode(self.pk) + ": " + self.id_on_provider + " @ " + unicode(self.provider)


# class DealManager(ShoutManager):
# def get_valid_deals(self, country=None, city=None, get_expired=False, get_muted=False):
#         return ShoutManager.get_valid_shouts(self, [POST_TYPE_DEAL], country=country, city=city, get_expired=get_expired, get_muted=get_muted)
#
#
# class ExperienceManager(PostManager):
#     def get_valid_experiences(self, country=None, city=None, get_muted=False):
#         return PostManager.get_valid_posts(self, types=[POST_TYPE_EXPERIENCE], country=country, city=city, get_expired=True, get_muted=get_muted)

# class Deal(Shout):
#     MinBuyers = models.IntegerField(default=0)
#     MaxBuyers = models.IntegerField(null=True, blank=True)
#     OriginalPrice = models.FloatField()
#     IsClosed = models.BooleanField(default=False)
#     ValidFrom = models.DateTimeField(null=True, blank=True)
#     ValidTo = models.DateTimeField(null=True, blank=True)
#
#     objects = DealManager()
#
#     def BuyersCount(self):
#         return self.Buys.aggregate(buys=Sum('Amount'))['buys']
#
#     def AvailableCount(self):
#         return self.MaxBuyers - self.BuyersCount()


# class Experience(Post):
#     AboutBusiness = models.ForeignKey('shoutit.Business', related_name='Experiences')
#     state = models.IntegerField(null=False)
#
#     objects = ExperienceManager()
#
#     def __unicode__(self):
#         return unicode(self.pk)
#
#
# class SharedExperience(UUIDModel):
#     Experience = models.ForeignKey('shoutit.Experience', related_name='SharedExperiences')
#     user = models.ForeignKey(AUTH_USER_MODEL, related_name='SharedExperiences')
#
#     class Meta(UUIDModel.Meta):
#         unique_together = ('Experience', 'user',)


# class Comment(UUIDModel):
#     AboutPost = models.ForeignKey('shoutit.Post', related_name='Comments', null=True, blank=True)
#     user = models.ForeignKey(AUTH_USER_MODEL, related_name='+')
#     is_disabled = models.BooleanField(default=False)
#     text = models.TextField(max_length=300)
#
#     def __unicode__(self):
#         return unicode(self.pk) + ": " + unicode(self.text)
