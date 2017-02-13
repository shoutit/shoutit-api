from collections import OrderedDict
from datetime import timedelta

from django.conf import settings
from django.contrib.contenttypes.fields import GenericRelation
from django.contrib.postgres.fields import HStoreField
from django.db import models
from django.db.models import Q
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from elasticsearch_dsl import DocType, String, Date, Double, Integer, Boolean, Object, MetaField

from common.constants import POST_TYPE_REQUEST, PostType
from common.utils import date_unix
from shoutit.models.action import Action
from shoutit.models.auth import InactiveUser
from shoutit.models.base import UUIDModel
from shoutit.utils import none_to_blank, correct_mobile

AUTH_USER_MODEL = getattr(settings, 'AUTH_USER_MODEL')
SHOUT_SELECT_RELATED = ('item', 'category__main_tag', 'item__currency', 'user__profile', 'user__page')
SHOUT_PREFETCH_RELATED = ('item__videos',)


class ShoutManager(models.Manager):
    def get_valid_shouts(self, types=None, country=None, state=None, city=None, get_expired=False, get_muted=False):
        qs = self.filter(is_disabled=False)
        if types:
            qs = qs.filter(type__in=types)
        if country:
            qs = qs.filter(country__iexact=country)
        if state:
            qs = qs.filter(state__iexact=state)
        if city:
            qs = qs.filter(city__iexact=city)
        if not get_muted:
            qs = qs.filter(is_muted=False)
        if not get_expired:
            qs = self.filter_expired_out(qs)
        qs = qs.select_related(*SHOUT_SELECT_RELATED).prefetch_related(*SHOUT_PREFETCH_RELATED)
        return qs

    def filter_expired_out(self, qs):
        now = timezone.now()
        min_published = now - timedelta(days=int(settings.MAX_EXPIRY_DAYS))

        # Recently published and no specified expires_at
        no_expiry_still_valid = Q(expires_at__isnull=True, published_at__gte=min_published)

        # Not expired
        expiry_still_valid = Q(expires_at__isnull=False, expires_at__gte=now)

        return qs.filter(no_expiry_still_valid | expiry_still_valid)


class Post(Action):
    text = models.TextField(max_length=10000, blank=True)
    type = models.IntegerField(choices=PostType.choices, default=POST_TYPE_REQUEST.value, db_index=True)
    published_at = models.DateTimeField(default=timezone.now, db_index=True)
    published_on = HStoreField(blank=True, default=dict)

    is_muted = models.BooleanField(default=False, db_index=True)
    is_disabled = models.BooleanField(default=False, db_index=True)

    priority = models.SmallIntegerField(default=0)

    def __init__(self, *args, **kwargs):
        super(Action, self).__init__(*args, **kwargs)
        self._meta.get_field('user').blank = False

    def clean(self):
        none_to_blank(self, ['text'])

    def mute(self):
        self.is_muted = True
        self.save(update_fields=['is_muted'])

    def unmute(self):
        self.is_muted = False
        self.save(update_fields=['is_muted'])

    @property
    def published_at_unix(self):
        return date_unix(self.published_at)

    @property
    def thumbnail(self):
        return self.item.thumbnail

    @property
    def video_url(self):
        return self.item.video_url


class Shout(Post):
    category = models.ForeignKey('shoutit.Category', related_name='shouts', null=True)
    tags = models.ManyToManyField('shoutit.Tag', blank=True, related_name='shouts')
    is_indexed = models.BooleanField(default=False, db_index=True)

    item = models.OneToOneField('shoutit.Item')

    expires_at = models.DateTimeField(null=True, blank=True, db_index=True)
    expiry_notified = models.BooleanField(default=False)
    renewal_count = models.PositiveSmallIntegerField(default=0)

    is_sss = models.BooleanField(default=False)
    mobile = models.CharField(blank=True, max_length=20, default='')

    bookmarked_by = models.ManyToManyField(AUTH_USER_MODEL, blank=True, through='ShoutBookmark',
                                           through_fields=('shout', 'user'), related_name='bookmarks')
    conversations = GenericRelation('shoutit.Conversation', related_query_name='about_shout')
    message_attachments = GenericRelation('shoutit.MessageAttachment', related_query_name='attached_shout')

    objects = ShoutManager()

    def __str__(self):
        return "%s: %s, %s: %s" % (self.pk, self.item, self.country, self.city)

    def clean(self):
        # Super clean
        super(Shout, self).clean()

        # Mobile
        if self.mobile:
            mobile_shout_country = correct_mobile(self.mobile, self.country)
            mobile_owner_country = correct_mobile(self.mobile, self.owner.ap.country)
            self.mobile = mobile_shout_country or mobile_owner_country
        none_to_blank(self, ['mobile'])

    @property
    def title(self):
        return self.item.name

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
    def is_expired(self):
        now = timezone.now()
        should_expire_at = self.published_at + timedelta(days=int(settings.MAX_EXPIRY_DAYS))
        no_expiry_invalid = self.expires_at is None and now > should_expire_at
        expiry_invalid = self.expires_at is not None and now > self.expires_at
        if no_expiry_invalid or expiry_invalid:
            return True
        return False

    @property
    def track_properties(self):
        properties = super(Shout, self).track_properties
        properties.update({
            'category': self.category.slug,
            'images': len(self.images),
            'videos': self.videos.count(),
            'price': self.item.price,
            'currency': self.item.currency.name if self.item.currency else None,
            'has_mobile': bool(self.mobile),
            'published_to_facebook': self.published_on.get('facebook'),
        })
        return properties

    @property
    def filters(self):
        _filters = []
        for tag in self.tags.all().select_related('key'):
            tag.key.value = tag
            _filters.append(tag.key)
        return _filters

    @property
    def mobile_hint(self):
        return (self.mobile[:5] + "...") if self.is_mobile_set else None

    @property
    def is_mobile_set(self):
        return bool(self.mobile)

    @property
    def promotion(self):
        return self.promotions.order_by('created_at').last()

    def is_bookmarked(self, user):
        return ShoutBookmark.exists(user=user, shout=self)

    def is_liked(self, user):
        return ShoutLike.exists(user=user, shout=self)


class InactiveShout(object):
    @property
    def to_dict(self):
        return OrderedDict({
            "id": "",
            "api_url": "",
            "web_url": "",
            "type": "",
            "location": {
                "latitude": 0, "longitude": 0, "country": "", "postal_code": "", "state": "", "city": "", "address": ""
            },
            "title": _("Deleted Shout"),
            "text": "",
            "price": 0,
            "currency": "",
            "thumbnail": "",
            "video_url": "",
            "user": InactiveUser().to_dict,
            "profile": InactiveUser().to_dict,
            "date_published": 0,
            "published_at": 0,
            "is_expired": True,
            "category": {"name": "", "slug": "", "main_tag": {}},
            "tags": [],
            "filters": []
        })


class ShoutIndex(DocType):
    # indexed
    type = String(index='not_analyzed')
    title = String(analyzer='snowball', fields={'raw': String(index='not_analyzed')})
    text = String(analyzer='snowball')
    tags = String(index='not_analyzed')
    filters = Object()
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
    is_muted = Boolean()
    uid = String(index='not_analyzed')
    username = String(index='not_analyzed')
    published_at = Date()
    expires_at = Date()

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
            # Todo (mo): disabled for now since we are filtering only on string values
            # {
            #     "filters_integer_keys": {
            #         "match_pattern": "regex",
            #         "match": "^(num_.*|.*size|.*length|.*width|.*area|.*vol|.*qty|.*speed|.*year|age|mileage|.*weight)$",
            #         "mapping": {
            #             "type": "integer"
            #         }
            #     }
            # },
            {
                "filters_string_keys": {
                    "path_match": "filters.*",
                    "mapping": {
                        "type": "string",
                        "index": "not_analyzed"
                    }
                }
            }
        ])

    @property
    def published_at_unix(self):
        return date_unix(self.published_at)


class Video(UUIDModel):
    url = models.URLField(max_length=1024)
    thumbnail_url = models.URLField(max_length=1024)
    provider = models.CharField(max_length=1024)
    id_on_provider = models.CharField(max_length=256)
    duration = models.PositiveIntegerField()

    def __str__(self):
        return "%s: %s @ %s" % (self.pk, self.id_on_provider, self.provider)


class ShoutLike(Action):
    shout = models.ForeignKey(Shout, related_name='likes')

    class Meta:
        unique_together = ('user', 'shout')

    @property
    def track_properties(self):
        properties = super(ShoutLike, self).track_properties
        properties.update({
            'shout': self.shout_id
        })
        return properties


class ShoutBookmark(Action):
    shout = models.ForeignKey(Shout, related_name='bookmarks')

    class Meta:
        unique_together = ('user', 'shout')

    @property
    def track_properties(self):
        properties = super(ShoutBookmark, self).track_properties
        properties.update({
            'shout': self.shout_id
        })
        return properties
