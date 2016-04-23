from __future__ import unicode_literals

from django.conf import settings
from django.db.models.query_utils import Q
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.translation import ugettext as _
from django_rq import job
from push_notifications.apns import APNSError
from push_notifications.gcm import GCMError
from push_notifications.models import APNSDevice, GCMDevice

from common.constants import (NOTIFICATION_TYPE_LISTEN, NOTIFICATION_TYPE_MESSAGE, DEVICE_ANDROID, DEVICE_IOS,
                              NOTIFICATION_TYPE_BROADCAST, NOTIFICATION_TYPE_VIDEO_CALL,
                              NOTIFICATION_TYPE_MISSED_VIDEO_CALL)
from ..models import User, PushBroadcast
from ..utils import debug_logger, serialize_attached_object


@job(settings.RQ_QUEUE_PUSH)
def send_push(user, notification_type, attached_object, version):
    from shoutit.controllers.notifications_controller import get_total_unread_count

    # Check whether we are really going to send anything
    sending_apns = user.has_apns and getattr(user.apns_device.devices.first(), 'api_version', None) == version
    sending_gcm = user.has_gcm and getattr(user.gcm_device.devices.first(), 'api_version', None) == version
    if not sending_apns and not sending_gcm:
        return

    # Serialize the attached object and prepare the message
    attached_object_dict = serialize_attached_object(attached_object=attached_object, version=version, user=user)

    if notification_type == NOTIFICATION_TYPE_LISTEN:
        name = attached_object.first_name
        message = _("%(name)s started listening to you") % {'name': name}
    elif notification_type == NOTIFICATION_TYPE_MESSAGE:
        name = attached_object.user.first_name if attached_object.user else 'Shoutit'
        text = attached_object.summary
        message = _("%(name)s: %(text)s") % {'name': name, 'text': text}
    else:
        message = None

    if version == 'v2':
        extra = {
            'notification_type': int(notification_type),
            'object': attached_object_dict
        }
    else:
        extra = {
            'event_name': str(notification_type),
            'data': attached_object_dict,
            'message': message
        }

    # Send the Push
    if sending_apns:
        badge = get_total_unread_count(user)
        try:
            user.apns_device.send_message(message, extra=extra, sound='default', badge=badge)
            debug_logger.debug("Sent %s APNS push to %s." % (version, user))
        except APNSError:
            debug_logger.warn("Could not send %s APNS push to %s." % (version, user), exc_info=True)

    if sending_gcm:
        try:
            user.gcm_device.send_message(message, extra=extra)
            debug_logger.debug("Sent %s GCM push to %s." % (version, user))
        except GCMError:
            debug_logger.warn("Could not send %s GCM push to %s." % (version, user), exc_info=True)


def send_incoming_video_call(user, from_user, version):

    if user.apns_device and getattr(user.apns_device.devices.first(), 'api_version', None) == version:
        alert = {
            "title": "Incoming video call",
            'body': "%s is calling you on Shoutit" % from_user.first_name,
            "action-loc-key": "Answer"
        }
        try:
            user.apns_device.send_message(message=alert, sound='default', category='VIDEO_CALL_CATEGORY')
            debug_logger.debug("Sent APNS Incoming video call push to %s." % user)
        except APNSError:
            debug_logger.warn("Could not send APNS Incoming video call push.", exc_info=True)

    if user.gcm_device and getattr(user.gcm_device.devices.first(), 'api_version', None) == version:
        extra = {
            'type': str(NOTIFICATION_TYPE_VIDEO_CALL),
            'message': "Incoming video call",
            'body': "%s is calling you on Shoutit" % from_user.first_name,
        }
        try:
            user.gcm_device.send_message(message=None, extra=extra)
            debug_logger.debug("Sent GCM Incoming video call push to %s." % user)
        except GCMError:
            debug_logger.warn("Could not GCM Incoming video call push push.", exc_info=True)


def send_missed_video_call(user, from_user, version):
    if user.apns_device and getattr(user.apns_device.devices.first(), 'api_version', None) == version:
        alert = {
            "title": "Missed video call",
            "body": "You missed a call from %s." % from_user.first_name,
        }
        try:
            user.apns_device.send_message(message=alert, sound='default')
            debug_logger.debug("Sent APNS Missed video call push to %s." % user)
        except APNSError:
            debug_logger.warn("Could not send APNS Missed video call push to %s." % user, exc_info=True)

    if user.gcm_device and getattr(user.gcm_device.devices.first(), 'api_version', None) == version:
        extra = {
            'type': str(NOTIFICATION_TYPE_MISSED_VIDEO_CALL),
            'message': "Missed video call",
            "body": "You missed a call from %s." % from_user.first_name,
        }
        try:
            user.gcm_device.send_message(message=None, extra=extra)
            debug_logger.debug("Sent GCM Missed video call push to %s." % user)
        except GCMError:
            debug_logger.warn("Could not send GCM Missed video call push to %s." % user, exc_info=True)


@job(settings.RQ_QUEUE_PUSH)
def set_ios_badge(user):
    from .notifications_controller import get_total_unread_count

    if user.apns_device:
        badge = get_total_unread_count(user)
        try:
            user.apns_device.send_message(message=None, badge=badge)
            debug_logger.debug("Set apns badge for %s." % user)
        except APNSError:
            debug_logger.warn("Could not set apns badge for.", exc_info=True)


def check_push(notification_type):
    if notification_type not in [NOTIFICATION_TYPE_LISTEN, NOTIFICATION_TYPE_MESSAGE]:
        return False
    return (not settings.DEBUG) or settings.FORCE_PUSH


@receiver(post_save, sender=PushBroadcast)
def post_save_push_broadcast(sender, instance=None, created=False, **kwargs):
    if not created:
        return
    prepare_push_broadcast.delay(instance)


@job(settings.RQ_QUEUE_PUSH_BROADCAST)
def prepare_push_broadcast(push_broadcast):
    users = User.objects.filter(~Q(accesstoken=None))
    countries = push_broadcast.conditions.get('countries', [])
    devices = push_broadcast.conditions.get('devices', [])
    user_ids = push_broadcast.conditions.get('user_ids', [])

    if not user_ids:
        if countries:
            users = users.filter(profile__country__in=countries)

        user_ids = list(users.values_list('id', flat=True))

    while len(user_ids) > settings.MAX_BROADCAST_RECIPIENTS:
        chunk = user_ids[-settings.MAX_BROADCAST_RECIPIENTS:]
        user_ids = user_ids[:-settings.MAX_BROADCAST_RECIPIENTS]
        send_push_broadcast.delay(push_broadcast, devices, UserIds(chunk))
    send_push_broadcast.delay(push_broadcast, devices, UserIds(user_ids))


@job(settings.RQ_QUEUE_PUSH_BROADCAST)
def send_push_broadcast(push_broadcast, devices, user_ids):
    assert isinstance(user_ids, list) and len(
        user_ids) <= settings.MAX_BROADCAST_RECIPIENTS, "user_ids shout be a list <= 1000"

    # Todo: Send for both v2 and v3
    if DEVICE_IOS.value in devices:
        apns_devices = APNSDevice.objects.filter(user__in=user_ids)
        apns_devices.send_message(push_broadcast.message, sound='default',
                                  extra={"notification_type": int(NOTIFICATION_TYPE_BROADCAST)})
        debug_logger.debug("Sent push broadcast: %s to %d apns devices" % (push_broadcast.pk, len(apns_devices)))
    if DEVICE_ANDROID.value in devices:
        gcm_devices = GCMDevice.objects.filter(user__in=user_ids)
        gcm_devices.send_message(push_broadcast.message, extra={"notification_type": int(NOTIFICATION_TYPE_BROADCAST)})
        debug_logger.debug("Sent push broadcast: %s to %d gcm devices" % (push_broadcast.pk, len(gcm_devices)))


class UserIds(list):
    def __repr__(self):
        return "UserIds: %d ids" % len(self)
