# -*- coding: utf-8 -*-
"""

"""
from __future__ import unicode_literals
from django.core.exceptions import ValidationError
from django.db import IntegrityError

from .models import *
from shoutit.utils import debug_logger


def create_channel(channel_name):
    if 'presence' in channel_name:
        channel_type = 2
    elif 'private' in channel_name:
        channel_type = 1
    else:
        channel_type = 0

    channel = PusherChannel(type=channel_type, name=channel_name)
    try:
        channel.save()
        debug_logger.debug('Created PusherChannel: %s' % channel_name)
    except (ValidationError, IntegrityError) as e:
        debug_logger.warn(e)
    return channel


def delete_channel(channel_name):
    PusherChannel.objects.filter(name=channel_name).delete()
    debug_logger.debug('Deleted PusherChannel: %s' % channel_name)


def add_member(channel_name, user_id):
    try:
        channel = PusherChannel.objects.get(name=channel_name)
    except PusherChannel.DoesNotExist:
        channel = create_channel(channel_name)

    try:
        PusherChannelJoin(channel=channel, user_id=user_id).save()
        debug_logger.debug('Added User: %s to PusherChannel: %s' % (user_id, channel.name))
    except (ValidationError, IntegrityError) as e:
        debug_logger.warn(e)


def remove_member(channel_name, user_id):
    PusherChannelJoin.objects.filter(channel__name=channel_name, user_id=user_id).delete()
    debug_logger.debug('Removed User: %s from PusherChannel: %s' % (user_id, channel_name))
