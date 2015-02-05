from django.db import models
from apps.shoutit.models.base import UUIDModel


class Item(UUIDModel):
    Name = models.CharField(max_length=512, default='', blank=True)
    Description = models.CharField(max_length=1000)
    Price = models.FloatField(default=0.0)
    Currency = models.ForeignKey('shoutit.Currency', related_name='Items')
    State = models.IntegerField(default=0, db_index=True)
    DateCreated = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return unicode(self.pk) + ": " + self.Name

    def get_images(self):
        if not hasattr(self, '_images'):
            self._images = list(self.Images.all().order_by('image'))
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
    Code = models.CharField(max_length=10)
    Country = models.CharField(max_length=10, blank=True)
    Name = models.CharField(max_length=64, null=True, blank=True)

    def __unicode__(self):
        return '[' + self.Code + '] '
