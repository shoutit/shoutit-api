from datetime import datetime
from django.contrib.contenttypes.models import ContentType
from django.db.models.query_utils import Q
from apps.shoutit.api.renderers import render_notification


def MarkAllAsRead(user):
    Notification.objects.filter(IsRead=False, ToUser=user).update(IsRead=True)


def NotifyUser(user, type, from_user=None, attached_object=None):
    pk = attached_object and attached_object.pk or None
    ct = attached_object and ContentType.objects.db_manager(attached_object._state.db).get_for_model(attached_object) or None
    notification, created = Notification.objects.get_or_create(ToUser = user, Type=type, FromUser=from_user, object_pk = pk, content_type=ct)
    if not created:
        notification.DateCreated = datetime.now()
        notification.IsRead = False
        notification.save()

    count = apps.shoutit.controllers.realtime_controller.GetUserConnectedClientsCount(user.username)
    if count:
        # todo: add the new push (apns/gcm)
        apps.shoutit.controllers.realtime_controller.SendNotification(notification, user.username, count)
        realtime_message = apps.shoutit.controllers.realtime_controller.WrapRealtimeMessage(render_notification(notification),RealtimeType.values[REALTIME_TYPE_NOTIFICATION])
        apps.shoutit.controllers.realtime_controller.SendRealtimeMessage(realtime_message, user.username)


def NotifyUserOfFollowship(user, follower):
    NotifyUser(user, NOTIFICATION_TYPE_FOLLOWSHIP, follower, follower)


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


from apps.shoutit.constants import NOTIFICATION_TYPE_FOLLOWSHIP, NOTIFICATION_TYPE_MESSAGE, NOTIFICATION_TYPE_EXP_POSTED, NOTIFICATION_TYPE_EXP_SHARED, NOTIFICATION_TYPE_COMMENT, RealtimeType, REALTIME_TYPE_NOTIFICATION
import apps.shoutit.controllers.realtime_controller
from apps.shoutit.models import Notification