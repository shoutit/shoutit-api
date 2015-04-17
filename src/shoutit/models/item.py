from __future__ import unicode_literals
from django.contrib.postgres.fields import ArrayField
from django.db import models
from common.constants import ITEM_STATE_AVAILABLE
from shoutit.models.base import UUIDModel


class Item(UUIDModel):
    name = models.CharField(max_length=512, default='', blank=True)
    description = models.CharField(max_length=1000)
    price = models.FloatField(default=0.0)
    currency = models.ForeignKey('shoutit.Currency', related_name='Items')
    state = models.IntegerField(default=ITEM_STATE_AVAILABLE.value, db_index=True)
    images = ArrayField(models.URLField(), null=True, blank=True)

    def __str__(self):
        return unicode(self.pk) + ": " + self.name

    @property
    def thumbnail(self):
        if self.videos.all():
            return self.videos.all()[0].thumbnail_url
        elif self.images:
            return self.images[0]
        else:
            return None

    @property
    def video_url(self):
        return self.videos.all()[0].url if self.videos.all() else None

    def get_videos(self):
        if not hasattr(self, '_videos'):
            self._videos = list(self.videos.all())
        return self._videos

    def set_videos(self, videos):
        self._videos = videos

    def get_first_video(self):
        videos = self.get_videos()
        return videos and videos[0] or None


class Currency(UUIDModel):
    code = models.CharField(max_length=10)
    country = models.CharField(max_length=10, blank=True)
    name = models.CharField(max_length=64, null=True, blank=True)

    def __str__(self):
        return '[' + self.code + '] '
