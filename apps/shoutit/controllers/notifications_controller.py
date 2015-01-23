from django.utils.translation import ugettext as _
from django.db.models.query_utils import Q
from push_notifications.apns import APNSError
from push_notifications.gcm import GCMError

from apps.shoutit.models import Notification
from apps.shoutit.api.renderers import render_notification, render_user, render_message
from common.constants import NOTIFICATION_TYPE_LISTEN, NOTIFICATION_TYPE_MESSAGE, NOTIFICATION_TYPE_EXP_POSTED, \
    NOTIFICATION_TYPE_EXP_SHARED, NOTIFICATION_TYPE_COMMENT, RealtimeType, REALTIME_TYPE_NOTIFICATION
from apps.shoutit.controllers import realtime_controller


def mark_all_as_read(user):
    Notification.objects.filter(IsRead=False, ToUser=user).update(IsRead=True)


def notify_user(user, notification_type, from_user=None, attached_object=None):
    notification = Notification(ToUser=user, Type=notification_type, FromUser=from_user, attached_object=attached_object)
    notification.save()

    count = realtime_controller.GetUserConnectedClientsCount(user.username)
    if count:
        realtime_controller.SendNotification(notification, user.username, count)
        realtime_message = realtime_controller.WrapRealtimeMessage(render_notification(notification),
                                                                   RealtimeType.values[REALTIME_TYPE_NOTIFICATION])
        realtime_controller.SendRealtimeMessage(realtime_message, user.username)

    if notification_type == NOTIFICATION_TYPE_LISTEN:
        message = _("You got a new listen")
        attached_object_dict = render_user(attached_object, 2)
    elif notification_type == NOTIFICATION_TYPE_MESSAGE:
        message = _("You got a new message")
        attached_object_dict = render_message(attached_object)
    else:
        message = None
        attached_object_dict = {}

    # new apns / gcm
    if user.apns_device:
        try:
            user.apns_device.send_message(message, badge=get_user_notifications_count(user), extra={
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


def notify_user_of_listen(user, listener):
    notify_user(user, NOTIFICATION_TYPE_LISTEN, listener, listener)


def notify_user_of_message(user, message):
    notify_user(user, NOTIFICATION_TYPE_MESSAGE, message.FromUser, message)


def notify_business_of_exp_posted(business, exp):
    notify_user(business, NOTIFICATION_TYPE_EXP_POSTED, from_user=exp.OwnerUser, attached_object=exp)


def notify_user_of_exp_shared(user, shared_exp):
    notify_user(user, NOTIFICATION_TYPE_EXP_SHARED, from_user=shared_exp.OwnerUser, attached_object=shared_exp)


def notify_users_of_comment(users, comment):
    for user in users:
        notify_user(user, NOTIFICATION_TYPE_COMMENT, from_user=comment.OwnerUser, attached_object=comment)


def get_user_notifications(user):
    return Notification.objects.filter(IsRead=False, ToUser=user)


def get_user_notifications_count(user):
    return Notification.objects.filter(IsRead=False, ToUser=user).count()


def get_user_notifications_without_messages_count(user):
    return Notification.objects.filter(Q(IsRead=False) & Q(ToUser=user) & ~Q(Type=NOTIFICATION_TYPE_MESSAGE)).count()
