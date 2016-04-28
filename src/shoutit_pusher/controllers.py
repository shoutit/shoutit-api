# -*- coding: utf-8 -*-
"""

"""
from __future__ import unicode_literals
from django.core.exceptions import ValidationError
from django.db import IntegrityError

from .models import *  # NOQA
from shoutit.utils import debug_logger


def create_channel(channel_name):
    if 'presence' in channel_name:
        channel_type = 2
    elif 'private' in channel_name:
        channel_type = 1
    else:
        channel_type = 0

    channel, created = PusherChannel.objects.get_or_create(type=channel_type, name=channel_name)
    if created:
        debug_logger.debug('Created PusherChannel: %s' % channel_name)
    return channel


def delete_channel(channel_name):
    channel = PusherChannel.objects.filter(name=channel_name)
    if channel.exists():
        channel.delete()
        debug_logger.debug('Deleted PusherChannel: %s' % channel_name)


def add_member(channel_name, user_id):
    channel = create_channel(channel_name)
    join, created = PusherChannelJoin.objects.get_or_create(channel=channel, user_id=user_id)
    if created:
        debug_logger.debug('Added Member: %s to PusherChannel: %s' % (user_id, channel.name))


def remove_member(channel_name, user_id):
    join = PusherChannelJoin.objects.filter(channel__name=channel_name, user_id=user_id)
    if join.exists():
        join.delete()
        debug_logger.debug('Removed Member: %s from PusherChannel: %s' % (user_id, channel_name))
        joins = PusherChannelJoin.objects.filter(channel__name=channel_name)
        if not joins.exists():
            delete_channel(channel_name)
