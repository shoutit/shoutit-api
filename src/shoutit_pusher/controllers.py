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

    try:
        channel = PusherChannel.create(type=channel_type, name=channel_name)
        debug_logger.debug('Created PusherChannel: %s' % channel_name)
        return channel
    except (ValidationError, IntegrityError) as e:
        debug_logger.warn(e)
        return None


def delete_channel(channel_name):
    try:
        channel = PusherChannel.objects.get(name=channel_name)
    except PusherChannel.DoesNotExist:
        pass
    else:
        channel.users.clear()
        channel.delete()
        debug_logger.debug('Deleted PusherChannel: %s' % channel_name)


def add_member(channel_name, user_id):
    try:
        channel = PusherChannel.objects.get(name=channel_name)
    except PusherChannel.DoesNotExist:
        channel = create_channel(channel_name)
    if channel:
        try:
            PusherChannelJoin.objects.create(channel=channel, user_id=user_id)
            debug_logger.debug('Added User: %s to PusherChannel: %s' % (user_id, channel.name))
        except IntegrityError as e:
            debug_logger.warn(e)


def remove_member(channel_name, user_id):
    PusherChannelJoin.objects.filter(channel__name=channel_name, user_id=user_id).delete()
    debug_logger.debug('Removed User: %s from PusherChannel: %s' % (user_id, channel_name))
