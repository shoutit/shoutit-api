# -*- coding: utf-8 -*-
"""

"""
from django.conf import settings
from django.core import validators
from django.db import models
from shoutit.models import UUIDModel
from pusher.util import channel_name_re, socket_id_re


class PusherDevice(UUIDModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL)
    socket_id = models.CharField(max_length=64, unique=True, validators=[
        validators.RegexValidator(socket_id_re)
    ])

    def __str__(self):
        return "%s: %s" % (str(self.user), self.socket_id)


pusher_channel_types = ((0, 'public'), (1, 'private'), (2, 'presence'))


# Todo: change PK to name
class PusherChannel(UUIDModel):
    type = models.SmallIntegerField(choices=pusher_channel_types)
    name = models.CharField(max_length=164, unique=True, validators=[
        validators.RegexValidator(channel_name_re)
    ])
    users = models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True, related_name='joined_pusher_channels',
                                   through='shoutit_pusher.PusherChannelJoin')

    def __str__(self):
        return "%s: %s users" % (self.name, self.users.count())

    @property
    def users_count(self):
        return self.users.count()


class PusherChannelJoin(UUIDModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL)
    channel = models.ForeignKey('shoutit_pusher.PusherChannel')

    class Meta:
        unique_together = ('user', 'channel')
