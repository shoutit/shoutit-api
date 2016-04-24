from __future__ import unicode_literals

from collections import OrderedDict
from datetime import timedelta

from django.conf import settings
from django.contrib.contenttypes.fields import GenericRelation
from django.contrib.postgres.fields import ArrayField, HStoreField
from django.db import models
from django.db.models import Q
from django.utils import timezone
from elasticsearch import RequestError, ConnectionTimeout
from elasticsearch_dsl import DocType, String, Date, Double, Integer, Boolean, Object, MetaField

from common.constants import (POST_TYPE_OFFER, POST_TYPE_REQUEST, PostType)
from common.utils import date_unix
from shoutit.models.action import Action
from shoutit.models.auth import InactiveUser
from shoutit.models.base import UUIDModel
from shoutit.models.tag import Tag, ShoutitSlugField
from shoutit.utils import error_logger, none_to_blank, correct_mobile

AUTH_USER_MODEL = getattr(settings, 'AUTH_USER_MODEL')


class PostManager(models.Manager):
    def get_valid_posts(self, types=None, country=None, city=None, get_expired=False, get_muted=False):
        qs = self.distinct().filter(is_disabled=False)
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
        return qs

    def filter_expired_out(self, qs):
        today = timezone.now()
        days = timedelta(days=int(settings.MAX_EXPIRY_DAYS))
        day = today - days
        return qs.filter(
            (Q(type=POST_TYPE_REQUEST) | Q(type=POST_TYPE_OFFER)) & (
                Q(shout__expiry_date__isnull=True, date_published__range=(day, today)) |
                Q(shout__expiry_date__isnull=False, shout__expiry_date__gte=today)
            )
        )


class ShoutManager(PostManager):
    def get_valid_shouts(self, types=None, country=None, city=None, get_expired=False, get_muted=False):
        if not types:
            types = [POST_TYPE_OFFER, POST_TYPE_REQUEST]
        types = list(set(types).intersection([POST_TYPE_OFFER, POST_TYPE_REQUEST]))
        return PostManager.get_valid_posts(self, types, country=country, city=city, get_expired=get_expired,
                                           get_muted=get_muted)

    def filter_expired_out(self, qs):
        today = timezone.now()
        days = timedelta(days=int(settings.MAX_EXPIRY_DAYS))
        day = today - days
        return qs.filter(Q(expiry_date__isnull=True, date_published__range=(day, today)) | Q(
            expiry_date__isnull=False, expiry_date__gte=today))

    def get_valid_requests(self, country=None, city=None, get_expired=False, get_muted=False):
        types = [POST_TYPE_REQUEST]
        return self.get_valid_shouts(types=types, country=country, city=city, get_expired=get_expired,
                                     get_muted=get_muted)

    def get_valid_offers(self, country=None, city=None, get_expired=False, get_muted=False):
        types = [POST_TYPE_OFFER]
        return self.get_valid_shouts(types=types, country=country, city=city, get_expired=get_expired,
                                     get_muted=get_muted)


class Post(Action):
    text = models.TextField(max_length=10000, blank=True)
    type = models.IntegerField(choices=PostType.choices, default=POST_TYPE_REQUEST.value, db_index=True)
    date_published = models.DateTimeField(default=timezone.now, db_index=True)
    published_on = HStoreField(blank=True, default=dict)

    muted = models.BooleanField(default=False, db_index=True)
    is_disabled = models.BooleanField(default=False, db_index=True)

    priority = models.SmallIntegerField(default=0)
    objects = PostManager()

    def __init__(self, *args, **kwargs):
        super(Action, self).__init__(*args, **kwargs)
        self._meta.get_field('user').blank = False

    def clean(self):
        super(Post, self).clean()
        none_to_blank(self, ['text'])

    def mute(self):
        self.muted = True
        self.save()

    def unmute(self):
        self.muted = False
        self.save()

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
    tags = ArrayField(ShoutitSlugField(), blank=True, default=list)
    tags2 = HStoreField(blank=True, default=dict)
    category = models.ForeignKey('shoutit.Category', related_name='shouts', null=True)
    is_indexed = models.BooleanField(default=False, db_index=True)

    item = models.OneToOneField('shoutit.Item', db_index=True)
    renewal_count = models.PositiveSmallIntegerField(default=0)

    expiry_date = models.DateTimeField(null=True, blank=True, default=None, db_index=True)
    expiry_notified = models.BooleanField(default=False)

    is_sss = models.BooleanField(default=False)
    mobile = models.CharField(blank=True, max_length=20, default='')
    conversations = GenericRelation('shoutit.Conversation', related_query_name='shout')

    objects = ShoutManager()

    def __unicode__(self):
        return unicode("%s: %s, %s: %s" % (self.pk, self.item.name, self.country, self.city))

    def clean(self):
        super(Shout, self).clean()
        if self.mobile:
            mobile_shout_country = correct_mobile(self.mobile, self.country)
            mobile_owner_country = correct_mobile(self.mobile, self.owner.ap.country)
            self.mobile = mobile_shout_country or mobile_owner_country
        none_to_blank(self, ['mobile'])

    @property
    def images(self):
        return self.item.images

    @property
    def videos(self):
        return self.item.videos.all()

    @property
    def available_count(self):
        return self.item.available_count

    @property
    def is_sold(self):
        return self.item.is_sold

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
        now = timezone.now()
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
            'id': self.pk,
            'profile': self.user_id,
            'type': self.get_type_display(),
            'category': self.category.slug,
            'Country': self.get_country_display(),
            'Region': self.state,
            'City': self.city,
            'images': len(self.images),
            'videos': self.videos.count(),
            'price': self.item.price,
            'currency': self.item.currency.name if self.item.currency else None,
            'has_mobile': bool(self.mobile),
            'published_to_facebook': self.published_on.get('facebook'),
            'api_client': getattr(self, 'api_client', None),
            'api_version': getattr(self, 'api_version', None),
        }

    @property
    def filters(self):
        filters = []
        for key, value in self.tags2.items():
            filters.append({
                'name': key.title() if isinstance(key, basestring) else key,
                'slug': key,
                'value': {
                    'name': value.title() if isinstance(value, basestring) else key,
                    'slug': value
                }
            })
        return filters

    @property
    def mobile_hint(self):
        return (self.mobile[:5] + "...") if self.is_mobile_set else None

    @property
    def is_mobile_set(self):
        return bool(self.mobile)


class InactiveShout(object):
    @property
    def to_dict(self):
        return OrderedDict({
            "id": "",
            "api_url": "",
            "web_url": "",
            "type": "offer",
            "location": {
                "latitude": 0, "longitude": 0, "country": "", "postal_code": "",
                "state": "", "city": "", "address": ""
            },
            "title": "Deleted Shout",
            "text": "",
            "price": 0,
            "currency": "",
            "thumbnail": "",
            "video_url": "",
            "user": InactiveUser().to_dict,
            "date_published": 0,
            "category": {"name": "", "slug": "", "main_tag": {}},
            "tags": [],
            "tags2": {}
        })


class ShoutIndex(DocType):
    # indexed
    type = String(index='not_analyzed')
    title = String(analyzer='snowball', fields={'raw': String(index='not_analyzed')})
    text = String(analyzer='snowball')
    tags_count = Integer()
    tags = String(index='not_analyzed')
    tags2 = Object()
    category = String(index='not_analyzed')
    country = String(index='not_analyzed')
    postal_code = String(index='not_analyzed')
    state = String(index='not_analyzed')
    city = String(index='not_analyzed')
    latitude = Double()
    longitude = Double()
    price = Double()
    available_count = Integer()
    is_sold = Boolean()
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
        index = '%s_shout' % settings.ES_BASE_INDEX
        dynamic_templates = MetaField([
            {
                "tags2_integer_keys": {
                    "match_pattern": "regex",
                    "match": "^(num_.*|.*size|.*length|.*width|.*area|.*vol|.*qty|.*speed|.*year|age|mileage|.*weight)$",
                    "mapping": {
                        "type": "integer"
                    }
                }
            },
            {
                "tags2_string_keys": {
                    "path_match": "tags2.*",
                    "mapping": {
                        "type": "string",
                        "index": "not_analyzed"
                    }
                }
            }
        ])

    @property
    def date_published_unix(self):
        return date_unix(self.date_published)


# initiate the index if not initiated
try:
    ShoutIndex.init()
except RequestError:
    pass
except ConnectionTimeout:
    error_logger.warn("ES Server is down.", exc_info=True)


class Video(UUIDModel):
    url = models.URLField(max_length=1024)
    thumbnail_url = models.URLField(max_length=1024)
    provider = models.CharField(max_length=1024)
    id_on_provider = models.CharField(max_length=256)
    duration = models.PositiveIntegerField()

    def __unicode__(self):
        return unicode(self.pk) + ": " + self.id_on_provider + " @ " + unicode(self.provider)
