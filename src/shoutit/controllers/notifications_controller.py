from __future__ import unicode_literals

from copy import deepcopy

from django.conf import settings
from django.db.models import Count
from django_rq import job
from rest_framework.settings import api_settings

from common.constants import (NOTIFICATION_TYPE_LISTEN, NOTIFICATION_TYPE_MESSAGE, NOTIFICATION_TYPE_PROFILE_UPDATE,
                              NOTIFICATION_TYPE_MISSED_VIDEO_CALL, NOTIFICATION_TYPE_INCOMING_VIDEO_CALL,
                              NOTIFICATION_TYPE_CREDIT_TRANSACTION, NOTIFICATION_TYPE_SHOUT_LIKE)
from shoutit.controllers import email_controller
from ..controllers import push_controller, pusher_controller
from ..models import Notification


def mark_all_as_read(user):
    """
    # Legacy: Mark Notifications of all types as read
    """
    Notification.objects.filter(is_read=False, to_user=user).update(is_read=True)
    pusher_controller.trigger_stats_update(user, 'v3')


def mark_actual_notifications_as_read(user):
    """
    Mark (actual) Notifications that are *not* of type `new_message` or `new_credit_transaction` as read
    """
    user.actual_notifications.filter(is_read=False).update(is_read=True)
    pusher_controller.trigger_stats_update(user, 'v3')


def mark_credit_transactions_as_read(user):
    """
    Mark Notifications that are of type `new_credit_transaction` as read
    """
    Notification.objects.filter(is_read=False, to_user=user, type=NOTIFICATION_TYPE_CREDIT_TRANSACTION).update(is_read=True)
    pusher_controller.trigger_stats_update(user, 'v3')


def get_total_unread_count(user):
    """
    Mainly used for setting iOS badge
    """
    return get_unread_actual_notifications_count(user) + get_unread_conversations_count(user)


def get_unread_actual_notifications_count(user):
    """
    Return count of unread (actual) Notifications that are *not* of type `new_message` or `new_credit_transaction`
    """
    return user.actual_notifications.filter(is_read=False).count()


def get_unread_conversations_count(user):
    """
    Return count of unique unread Conversations
    """
    q = Notification.objects.filter(is_read=False, to_user=user, type=NOTIFICATION_TYPE_MESSAGE)
    q = q.aggregate(count=Count('message__conversation', distinct=True))
    return q.get('count', 0)


@job(settings.RQ_QUEUE)
def notify_user(user, notification_type, from_user=None, attached_object=None, versions=None, serializing_options=None):
    if not versions:
        versions = api_settings.ALLOWED_VERSIONS

    # Create notification object
    notification = Notification(to_user=user, type=notification_type, from_user=from_user, attached_object=attached_object)

    if notification_type.requires_notification_object():
        # Save the notification
        notification.save()
        # Trigger `stats_update` on Pusher (introduced in v3)
        pusher_controller.trigger_stats_update(user, 'v3')

    # Send Push notification when no pusher channels of any version exist
    can_push = push_controller.check_push(notification_type)
    can_pusher = pusher_controller.check_pusher(user)
    if can_push and not can_pusher:
        for v in versions:
            push_controller.send_push.delay(user=user, notification=notification, version=v,
                                            serializing_options=serializing_options)

    # Trigger event on Pusher profile channel
    for v in versions:
        pusher_controller.trigger_profile_event(user=user, event_name=notification.event_name,
                                                attached_object=notification.event_object, version=v,
                                                serializing_options=serializing_options)

    # Send notification email
    if notification_type.include_in_email():
        email_controller.send_notification_email(user, notification)


def notify_user_of_listen(user, listener):
    notify_user.delay(user, notification_type=NOTIFICATION_TYPE_LISTEN, from_user=listener, attached_object=listener)


def notify_user_of_message(user, message):
    from_user = message.user
    notify_user.delay(user, notification_type=NOTIFICATION_TYPE_MESSAGE, from_user=from_user, attached_object=message)


def notify_user_of_profile_update(user):
    serializing_options = {'detailed': True}
    notify_user.delay(user, notification_type=NOTIFICATION_TYPE_PROFILE_UPDATE, attached_object=user, versions=['v3'],
                      serializing_options=serializing_options)


def notify_user_of_incoming_video_call(user, caller):
    notify_user.delay(user, notification_type=NOTIFICATION_TYPE_INCOMING_VIDEO_CALL, from_user=caller,
                      attached_object=caller, versions=['v3'])


def notify_user_of_missed_video_call(user, caller):
    notify_user.delay(user, notification_type=NOTIFICATION_TYPE_MISSED_VIDEO_CALL, from_user=caller,
                      attached_object=caller, versions=['v3'])


def notify_user_of_credit_transaction(transaction):
    notify_user.delay(transaction.user, notification_type=NOTIFICATION_TYPE_CREDIT_TRANSACTION,
                      attached_object=transaction, versions=['v3'])


def notify_shout_owner_of_shout_like(shout, user):
    notify_user.delay(shout.owner, notification_type=NOTIFICATION_TYPE_SHOUT_LIKE, from_user=user, attached_object=user,
                      versions=['v3'])
