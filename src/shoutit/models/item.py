from __future__ import unicode_literals
from django.contrib.postgres.fields import ArrayField
from django.db import models
from common.constants import ITEM_STATE_AVAILABLE
from shoutit.models.base import UUIDModel


class Item(UUIDModel):
    name = models.CharField(max_length=500)
    description = models.TextField(max_length=2000)
    price = models.FloatField(default=0, null=True, blank=True)
    currency = models.ForeignKey('shoutit.Currency', null=True, blank=True)
    state = models.IntegerField(default=ITEM_STATE_AVAILABLE.value, db_index=True)
    images = ArrayField(models.URLField(), default=list, blank=True)
    videos = models.ManyToManyField('shoutit.Video', blank=True)

    def __unicode__(self):
        return unicode(self.name[:30])

    @property
    def thumbnail(self):
        if self.images:
            return self.images[0]
        elif self.videos.all():
            return self.videos.all()[0].thumbnail_url
        else:
            return None

    @property
    def video_url(self):
        return self.videos.all()[0].url if self.videos.all() else None

    @property
    def currency_code(self):
        return self.currency.code if self.currency else None


class Currency(UUIDModel):
    code = models.CharField(max_length=10)
    country = models.CharField(max_length=10, blank=True)
    name = models.CharField(max_length=64, null=True, blank=True)

    def __unicode__(self):
        return '[' + self.code + '] '
