from django.db import models
from apps.shoutit.models.misc import UUIDModel


class Item(UUIDModel):
    class Meta:
        app_label = 'shoutit'

    def __unicode__(self):
        return unicode(self.pk) + ": " + self.Name

    Name = models.CharField(max_length=512, default='')
    Description = models.CharField(max_length=1000, default='')
    Price = models.FloatField(default=0.0)
    Currency = models.ForeignKey('Currency', related_name='Items')
    State = models.IntegerField(default=0, db_index=True)
    DateCreated = models.DateTimeField(auto_now_add=True)

    def GetImages(self):
        if hasattr(self, 'images'):
            return self.images
        else:
            self.images = list(self.Images.all().order_by('Image'))
            return self.images

    def SetImages(self, images):
        images = sorted(images, key=lambda img: img.Image)
        self.images = images

    def GetFirstImage(self):
        return self.GetImages() and self.GetImages()[0] or None

    def get_videos(self):
        if hasattr(self, '_videos'):
            return self._videos
        else:
            self._videos = list(self.videos.all())
            return self._videos

    def set_videos(self, videos):
        self._videos = videos

    #TODO
    def get_first_video(self):
        pass


class Currency(UUIDModel):
    class Meta:
        app_label = 'shoutit'

    def __unicode__(self):
        return '[' + self.Code + '] '

    Code = models.CharField(max_length=10)
    Country = models.CharField(max_length=10, blank=True)
    Name = models.CharField(max_length=64, null=True)
