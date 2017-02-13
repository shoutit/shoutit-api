"""

"""
from datetime import timedelta
from django.conf import settings
from django.db import models

from shoutit.models import UUIDModel
from .settings import SHOUTIT_TWILIO_SETTINGS


class VideoClient(UUIDModel):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, related_name='video_client')
    token = models.CharField(max_length=1000)
    ttl = models.IntegerField(default=SHOUTIT_TWILIO_SETTINGS['TOKEN_TTL'])

    def __str__(self):
        return "%s" % str(self.user)

    @property
    def identity(self):
        return self.id.hex

    @property
    def expires_at_unix(self):
        return self.created_at_unix + self.ttl

    @property
    def expires_at(self):
        return self.created_at + timedelta(seconds=self.ttl)
