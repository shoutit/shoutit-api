from __future__ import unicode_literals

from django.conf import settings
from django.db.models import Q
from django_rq import job

from common.constants import (NOTIFICATION_TYPE_MESSAGE, NOTIFICATION_TYPE_READ_BY,
                              NOTIFICATION_TYPE_CONVERSATION_UPDATE, NOTIFICATION_TYPE_STATS_UPDATE)
from shoutit_pusher.utils import pusher
from ..utils import serialize_attached_object, debug_logger


@job(settings.RQ_QUEUE_PUSHER)
def trigger_event(channel_name, notification_type, attached_object, version, user=None):
    """
    Trigger event on Pusher profile channel
    """
    event_name = str(notification_type)
    attached_object_dict = serialize_attached_object(attached_object=attached_object, version=version, user=user)
    pusher.trigger(channel_name, event_name, attached_object_dict)
    debug_logger.debug("Sent Pusher event: %s in channel: %s" % (event_name, channel_name))


def trigger_profile_event(user, notification_type, attached_object, version):
    """
    Trigger event on Pusher profile channel
    """
    if version == 'v2':
        channel_name = 'presence-u-%s' % user.pk
    else:
        channel_name = 'presence-%s-p-%s' % (version, user.pk)
    trigger_event.delay(channel_name, notification_type, attached_object, version, user)


def trigger_conversation_event(conversation_id, notification_type, attached_object, version):
    """
    Trigger event on Pusher conversation channel
    """
    channel_name = 'presence-%s-c-%s' % (version, conversation_id)
    trigger_event.delay(channel_name, notification_type, attached_object, version)


def trigger_stats_update(user, version):
    """
    Trigger `stats_update` event on Pusher conversation channel
    """
    trigger_profile_event(user, NOTIFICATION_TYPE_STATS_UPDATE, user.stats, version)

    # iOS needs special care! set its badge
    from .push_controller import set_ios_badge
    set_ios_badge.delay(user)


def trigger_new_message(message, version):
    """
    Trigger `new_message` event on Pusher conversation channel
    """
    trigger_conversation_event(message.conversation_id, NOTIFICATION_TYPE_MESSAGE, message, version)


def trigger_new_read_by(message, version):
    """
    Trigger `new_read_by` event on Pusher conversation channel
    """
    message_summary = {
        'id': message.id,
        'read_by': message.read_by_objects
    }
    trigger_conversation_event(message.conversation_id, NOTIFICATION_TYPE_READ_BY, message_summary, version)


def trigger_conversation_update(conversation, version):
    """
    Trigger `conversation_update` event on Pusher conversation channel
    """
    trigger_conversation_event(conversation.id, NOTIFICATION_TYPE_CONVERSATION_UPDATE, conversation, version)


def check_pusher(user):
    """
    Return whether a profile pusher channel exists for this user on any version
    """
    channel_name = Q(name='presence-u-%s' % user.pk)
    channel_name |= Q(name='presence-%s-p-%s' % ('v3', user.pk))
    return user.joined_pusher_channels.filter(channel_name).exists()
