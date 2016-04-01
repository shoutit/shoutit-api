"""

"""
from __future__ import unicode_literals

from django.conf import settings
from django.db import models

from shoutit.models import UUIDModel


class VideoClient(UUIDModel):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, related_name='video_client')
    token = models.CharField(max_length=1000)

    def __unicode__(self):
        return "%s" % unicode(self.user)

    @property
    def identity(self):
        return self.id.hex
