from __future__ import unicode_literals

from copy import deepcopy

from django.conf import settings
from django.db.models import Count
from django.db.models.query_utils import Q
from django_rq import job

from common.constants import (NOTIFICATION_TYPE_LISTEN, NOTIFICATION_TYPE_MESSAGE, NOTIFICATION_TYPE_PROFILE_UPDATE)
from ..controllers import push_controller, pusher_controller
from ..models import Notification


def mark_all_as_read(user):
    Notification.objects.filter(is_read=False, to_user=user).update(is_read=True)
    pusher_controller.trigger_stats_update(user, 'v3')


def mark_all_notifications_as_read(user):
    Notification.objects.filter(is_read=False, to_user=user).exclude(type=NOTIFICATION_TYPE_MESSAGE).update(is_read=True)
    pusher_controller.trigger_stats_update(user, 'v3')


def get_all_unread_notifications_count(user):
    return Notification.objects.filter(is_read=False, to_user=user).count()


def get_unread_notifications_count(user):
    return Notification.objects.filter(Q(is_read=False) & Q(to_user=user) & ~Q(type=NOTIFICATION_TYPE_MESSAGE)).count()


def get_unread_conversations_count(user):
    q = Notification.objects.filter(is_read=False, to_user=user, type=NOTIFICATION_TYPE_MESSAGE)
    q = q.aggregate(count=Count('message__conversation', distinct=True))
    return q.get('count', 0)


@job(settings.RQ_QUEUE)
def notify_user(user, notification_type, from_user=None, attached_object=None):
    # Trigger event on Pusher profile channel
    pusher_controller.trigger_profile_event(user, notification_type, attached_object, 'v2')
    pusher_controller.trigger_profile_event(user, notification_type, attached_object, 'v3')

    # Create notification object
    if notification_type != NOTIFICATION_TYPE_PROFILE_UPDATE:
        Notification.create(to_user=user, type=notification_type, from_user=from_user, attached_object=attached_object)

    # Trigger `stats_update` on Pusher
    pusher_controller.trigger_stats_update(user, 'v3')

    # Send Push notification when no pusher channels of any version exit
    if push_controller.check_push(notification_type) and not pusher_controller.check_pusher(user):
        push_controller.send_push.delay(user, notification_type, attached_object, 'v2')
        push_controller.send_push.delay(user, notification_type, attached_object, 'v3')


def notify_user_of_listen(user, listener):
    listener = deepcopy(listener)
    notify_user.delay(user, notification_type=NOTIFICATION_TYPE_LISTEN, from_user=listener, attached_object=listener)


def notify_user_of_message(user, message):
    from_user = deepcopy(message.user)
    notify_user.delay(user, notification_type=NOTIFICATION_TYPE_MESSAGE, from_user=from_user, attached_object=message)


def notify_user_of_profile_update(user):
    user.detailed = True
    attached_object = deepcopy(user)
    notify_user.delay(user, notification_type=NOTIFICATION_TYPE_PROFILE_UPDATE, attached_object=attached_object)
