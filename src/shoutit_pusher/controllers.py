# -*- coding: utf-8 -*-
"""

"""
from __future__ import unicode_literals

from django.db import IntegrityError

from shoutit.utils import debug_logger
from .models import *  # NOQA


def create_channel(channel_name):
    if 'presence' in channel_name:
        channel_type = 2
    elif 'private' in channel_name:
        channel_type = 1
    else:
        channel_type = 0

    channel, created = PusherChannel.objects.get_or_create(type=channel_type, name=channel_name)
    if created:
        debug_logger.debug('Created PusherChannel %s' % channel_name)
    else:
        debug_logger.debug('PusherChannel %s was already created' % channel_name)
    return channel


def delete_channel(channel_name):
    joins = PusherChannelJoin.objects.filter(channel__name=channel_name)
    if not joins.exists():
        channel = PusherChannel.objects.filter(name=channel_name)
        if channel.exists():
            try:
                channel.delete()
            except IntegrityError:
                debug_logger.debug('Could not delete PusherChannel %s' % channel_name)
            else:
                debug_logger.debug('Deleted PusherChannel %s' % channel_name)


def add_member(channel_name, user_id):
    channel = create_channel(channel_name)
    try:
        join, created = PusherChannelJoin.objects.get_or_create(channel=channel, user_id=user_id)
    except IntegrityError:
        # Another call has deleted the channel already
        pass
    else:
        if created:
            debug_logger.debug('Added Member %s to PusherChannel %s' % (user_id, channel.name))
        else:
            debug_logger.debug('Member %s was already added to PusherChannel %s' % (user_id, channel.name))


def remove_member(channel_name, user_id):
    join = PusherChannelJoin.objects.filter(channel__name=channel_name, user_id=user_id)
    if join.exists():
        join.delete()
        debug_logger.debug('Removed Member %s from PusherChannel %s' % (user_id, channel_name))
        # Try to delete the channel
        delete_channel(channel_name)
