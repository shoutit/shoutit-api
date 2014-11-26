from django.utils.translation import ugettext as _
from apps.shoutit.models import Notification
from datetime import datetime
from django.contrib.contenttypes.models import ContentType
from django.db.models.query_utils import Q
from apps.shoutit.api.renderers import render_notification
from apps.shoutit.constants import NOTIFICATION_TYPE_LISTEN, NOTIFICATION_TYPE_MESSAGE, NOTIFICATION_TYPE_EXP_POSTED, NOTIFICATION_TYPE_EXP_SHARED, NOTIFICATION_TYPE_COMMENT, RealtimeType, REALTIME_TYPE_NOTIFICATION
from apps.shoutit.controllers import realtime_controller


def MarkAllAsRead(user):
    Notification.objects.filter(IsRead=False, ToUser=user).update(IsRead=True)


def NotifyUser(user, notification_type, from_user=None, attached_object=None):
    notification, created = Notification.objects.get_or_create(ToUser=user, Type=notification_type, FromUser=from_user,
                                                               attached_object=attached_object)
    if not created:
        notification.DateCreated = datetime.now()
        notification.IsRead = False
        notification.save()

    count = realtime_controller.GetUserConnectedClientsCount(user.username)
    if count:
        # todo: add the new push (apns/gcm)
        realtime_controller.SendNotification(notification, user.username, count)
        realtime_message = realtime_controller.WrapRealtimeMessage(render_notification(notification), RealtimeType.values[REALTIME_TYPE_NOTIFICATION])
        realtime_controller.SendRealtimeMessage(realtime_message, user.username)

    if notification_type == NOTIFICATION_TYPE_LISTEN:
        message = _("You got a new lister")
    elif notification_type == NOTIFICATION_TYPE_MESSAGE:
        message = _("You got a new message")
    else:
        message = None

    # new apns / gcm
    if user.apns_device:
        user.apns_device.send_message(message, extra={
            'notification_type': notification_type,
            'object': attached_object
        })

    if user.gcm_device:
        user.gcm_device.send_message(message, extra={
            'notification_type': notification_type,
            'object': attached_object
        })


def NotifyUserOfListen(user, listener):
    NotifyUser(user, NOTIFICATION_TYPE_LISTEN, listener, listener)


def NotifyUserOfMessage(user, message):
    NotifyUser(user, NOTIFICATION_TYPE_MESSAGE, message.FromUser, message)


def NotifyBusinessOfExpPosted(business, exp):
    NotifyUser(business, NOTIFICATION_TYPE_EXP_POSTED, from_user = exp.OwnerUser, attached_object = exp)


def NotifyUserOfExpShared(user, shared_exp):
    NotifyUser(user, NOTIFICATION_TYPE_EXP_SHARED ,from_user=shared_exp.OwnerUser ,attached_object = shared_exp)


def NotifyUsersOfComment(users,comment):
    for user in users:
        NotifyUser(user, NOTIFICATION_TYPE_COMMENT,from_user=comment.OwnerUser, attached_object=comment)


def GetUserNotifications(user):
    return Notification.objects.filter(IsRead=False, ToUser=user)


def GetUserNotificationsWithoutMessagesCount(user):
    return Notification.objects.filter( Q(IsRead=False) & Q(ToUser=user) & ~Q(Type = NOTIFICATION_TYPE_MESSAGE)).count()
