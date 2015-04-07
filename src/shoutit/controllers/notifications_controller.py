from django.conf import settings
from django.utils.translation import ugettext as _
from django.db.models.query_utils import Q
from push_notifications.apns import APNSError
from push_notifications.gcm import GCMError
from django_rq import job

from common.constants import NOTIFICATION_TYPE_LISTEN, NOTIFICATION_TYPE_MESSAGE, NOTIFICATION_TYPE_EXP_POSTED, \
    NOTIFICATION_TYPE_EXP_SHARED, NOTIFICATION_TYPE_COMMENT

from shoutit.models import Notification, Message2


def mark_all_as_read(user):
    Notification.objects.filter(is_read=False, ToUser=user).update(is_read=True)


def mark_notifications_as_read_by_ids(notification_ids):
    Notification.objects.filter(id__in=notification_ids).update(is_read=True)


@job(settings.RQ_QUEUE)
def notify_user(user, notification_type, from_user=None, attached_object=None, request=None):
    from shoutit.api.v2 import serializers

    notification = Notification(ToUser=user, type=notification_type, FromUser=from_user, attached_object=attached_object)
    notification.save()

    if notification_type == NOTIFICATION_TYPE_LISTEN:
        message = _("You got a new listen")
        attached_object_dict = serializers.UserSerializer(attached_object, context={'request': request}).data
    elif notification_type == NOTIFICATION_TYPE_MESSAGE:
        message = _("You got a new message")
        if isinstance(attached_object, Message2):
            attached_object_dict = serializers.MessageSerializer(attached_object, context={'request': request}).data
        else:
            attached_object_dict = {}
    else:
        message = None
        attached_object_dict = {}

    if user.apns_device:
        try:
            user.apns_device.send_message(message, sound='default', badge=get_user_notifications_count(user), extra={
                'notification_type': int(notification_type),
                'object': attached_object_dict
            })
        except APNSError, e:
            print "Error: Could not send apns push to user %s." % user.username
            print "APNSError:", e

    if user.gcm_device:
        try:
            user.gcm_device.send_message(message, extra={
                'notification_type': int(notification_type),
                'object': attached_object_dict
            })
        except GCMError, e:
            print "Error: Could not send gcm push to user %s." % user.username
            print "GCMError:", e


def notify_user_of_listen(user, listener, request=None):
    notify_user.delay(user, NOTIFICATION_TYPE_LISTEN, listener, listener, request)


def notify_user_of_message(user, message):
    notify_user.delay(user, NOTIFICATION_TYPE_MESSAGE, message.FromUser, message)


def notify_user_of_message2(user, message, request=None):
    notify_user.delay(user, NOTIFICATION_TYPE_MESSAGE, message.user, message, request)


def notify_business_of_exp_posted(business, exp):
    notify_user.delay(business, NOTIFICATION_TYPE_EXP_POSTED, from_user=exp.user, attached_object=exp)


def notify_user_of_exp_shared(user, shared_exp):
    notify_user.delay(user, NOTIFICATION_TYPE_EXP_SHARED, from_user=shared_exp.user, attached_object=shared_exp)


def notify_users_of_comment(users, comment):
    for user in users:
        notify_user.delay(user, NOTIFICATION_TYPE_COMMENT, from_user=comment.user, attached_object=comment)


def get_user_notifications(user):
    return Notification.objects.filter(is_read=False, ToUser=user)


def get_user_notifications_count(user):
    return Notification.objects.filter(is_read=False, ToUser=user).count()


def get_user_notifications_without_messages_count(user):
    return Notification.objects.filter(Q(is_read=False) & Q(ToUser=user) & ~Q(type=NOTIFICATION_TYPE_MESSAGE)).count()
