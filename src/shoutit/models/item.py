from __future__ import unicode_literals
from django.db import models

from shoutit.models.base import UUIDModel


class Item(UUIDModel):
    name = models.CharField(max_length=512, default='', blank=True)
    Description = models.CharField(max_length=1000)
    Price = models.FloatField(default=0.0)
    Currency = models.ForeignKey('shoutit.Currency', related_name='Items')
    State = models.IntegerField(default=0, db_index=True)
    DateCreated = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return unicode(self.pk) + ": " + self.name

    @property
    def thumbnail(self):
        if self.get_videos():
            return self.get_videos()[0].thumbnail_url
        elif self.get_images():
            return self.get_images()[0].image
        else:
            return None

    @property
    def video_url(self):
        return self.get_first_video().url if self.get_first_video() else None

    def get_image_urls(self):
        return [image.image for image in self.get_images()]

    def get_images(self):
        if not hasattr(self, '_images'):
            self._images = list(self.images.all().order_by('image'))
        return self._images

    def set_images(self, images):
        images = sorted(images, key=lambda img: img.image)
        self._images = images

    def get_first_image(self):
        images = self.get_images()
        return images and images[0] or None

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
