from django.db import models
from apps.shoutit.models import Shout, Item


class Video(models.Model):
    class Meta:
        app_label = 'shoutit'

    def __unicode__(self):
        return unicode(self.id) + ": " + self.id_on_provider + " @ " + unicode(self.provider) + " for: " + unicode(self.item)

    shout = models.ForeignKey(Shout, related_name='videos', null=True)
    item = models.ForeignKey(Item, related_name='videos', null=True)

    url = models.URLField(max_length=1024)
    thumbnail_url = models.URLField(max_length=1024)
    provider = models.CharField(max_length=1024)
    id_on_provider = models.CharField(max_length=256)
    duration = models.IntegerField(default=0)


