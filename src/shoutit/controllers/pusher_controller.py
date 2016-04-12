from __future__ import unicode_literals

from django.conf import settings
from django_rq import job

from common.constants import (NOTIFICATION_TYPE_MESSAGE, NOTIFICATION_TYPE_READ_BY,
                              NOTIFICATION_TYPE_CONVERSATION_UPDATE)
from shoutit_pusher.models import PusherChannel
from shoutit_pusher.utils import pusher
from ..utils import serialize_attached_object


@job(settings.RQ_QUEUE_PUSHER)
def trigger_event(channel_name, notification_type, attached_object, version, user=None):
    """
    Trigger event on Pusher profile channel
    """
    attached_object_dict = serialize_attached_object(attached_object=attached_object, version=version, user=user)
    pusher.trigger(channel_name, str(notification_type), attached_object_dict)


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


def trigger_new_message(message, version):
    """
    Trigger `new_message` event on Pusher conversation channel
    """
    trigger_conversation_event(message.conversation_id, NOTIFICATION_TYPE_MESSAGE, message, version)


def trigger_new_read_by(message, version):
    """
    Trigger `new_read_by` event on Pusher conversation channel
    """
    trigger_conversation_event(message.conversation_id, NOTIFICATION_TYPE_READ_BY, message.read_by_objects, version)


def trigger_conversation_update(conversation, version):
    """
    Trigger `conversation_update` event on Pusher conversation channel
    """
    trigger_conversation_event(conversation.id, NOTIFICATION_TYPE_CONVERSATION_UPDATE, conversation, version)


def check_pusher_v2(user):
    """
    Return whether a v2 user pusher channel exits for this user
    """
    user_channel = 'presence-u-%s' % user.pk
    return PusherChannel.exists(name__iendswith=user_channel)


def check_pusher(user, version):
    """
    Return whether a profile pusher channel exists for this user
    """
    channel_name = 'presence-%s-p-%s' % (version, user.pk)
    return PusherChannel.exists(name__iendswith=channel_name)
