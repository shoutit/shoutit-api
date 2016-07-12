from __future__ import unicode_literals

from django.conf import settings
from django.contrib.contenttypes.fields import GenericRelation
from django.db.models.query_utils import Q
from django.db.models.signals import post_save
from django.dispatch import receiver
from django_rq import job
from push_notifications.apns import APNSError
from push_notifications.gcm import GCMError
from push_notifications.models import APNSDevice, GCMDevice
from rest_framework.settings import api_settings

from common.constants import (DEVICE_ANDROID, DEVICE_IOS, NotificationType, NOTIFICATION_TYPE_BROADCAST, USER_TYPE_PAGE,
                              NOTIFICATION_TYPE_INCOMING_VIDEO_CALL)
from shoutit.api.serializers import serialize_attached_object
from ..models import User, PushBroadcast, Device
from ..utils import debug_logger, error_logger, UserIds


_apns_devices = GenericRelation('shoutit.Device', related_query_name='apns_devices')
APNSDevice.add_to_class('devices', _apns_devices)

_gcm_devices = GenericRelation('shoutit.Device', related_query_name='gcm_devices')
GCMDevice.add_to_class('devices', _gcm_devices)


@job(settings.RQ_QUEUE_PUSH)
def send_push(user, notification, version, pushed_for=None, serializing_options=None):
    from shoutit.controllers.notifications_controller import get_total_unread_count

    # Notify the page admins if the notified user is a Page
    if user.type == USER_TYPE_PAGE:
        for admin in user.page.admins.all():
            send_push.delay(admin, notification, version, pushed_for=user)
        return

    # Check whether we are really going to send anything
    sending_apns = user.has_apns and getattr(user.apns_device.devices.first(), 'api_version', None) == version
    sending_gcm = user.has_gcm and getattr(user.gcm_device.devices.first(), 'api_version', None) == version
    if not sending_apns and not sending_gcm:
        return

    # Prepare the push object
    event_name = notification.push_event_name
    notification_display = notification.display()
    title = notification_display['title']
    body = notification_display['text']
    image = notification_display['image']
    alert_extra = notification_display.get('alert_extra', {})
    aps_extra = notification_display.get('aps_extra', {})
    data = serialize_attached_object(attached_object=notification.push_event_object, version=version,
                                     user=pushed_for or user, serializing_options=serializing_options)

    # Todo (mo): Make sure this doesn't break anything!
    # Todo (mo): Maybe we don't need to serialize attached objects here, app_url should be enough in most cases
    # Keep `app_url` only except for incoming_video_call notifications which have the caller profile properties
    if notification.type != NOTIFICATION_TYPE_INCOMING_VIDEO_CALL:
        data = {
            'app_url': data.get('app_url'),
        }

    # Send the Push
    if sending_apns:
        ios_extra = {
            'event_name': event_name,
            'data': data,
            'pushed_for': pushed_for.id if pushed_for else user.id,
        }
        badge = get_total_unread_count(user)
        alert = {
            'title': title,
            'body': body,
        }
        alert.update(alert_extra)
        aps = {
            'sound': 'default',
            'badge': badge
        }
        aps.update(aps_extra)
        try:
            user.send_apns(alert=alert, extra=ios_extra, **aps)
            debug_logger.debug("Sent %s APNS:%s to %s, pushed for %s" % (version, event_name, user, pushed_for))
        except APNSError:
            error_logger.warn("Could not send %s APNS:%s to %s, pushed for %s" % (version, event_name, user, pushed_for), exc_info=True)

    if sending_gcm:
        gcm_extra = {
            'event_name': event_name,
            'title': title,
            'body': body,
            'icon': image,
            'data': data,
            'pushed_for': pushed_for.id if pushed_for else user.id,
            # Todo: Deprecate legacy properties
            'type': str(notification.type),
            'message': body
        }

        try:
            user.send_gcm(data=gcm_extra)
            debug_logger.debug("Sent %s GCM:%s to %s, pushed for %s" % (version, event_name, user, pushed_for))
        except GCMError:
            error_logger.warn("Could not send %s GCM:%s to %s, pushed for %s" % (version, event_name, user, pushed_for), exc_info=True)


@job(settings.RQ_QUEUE_PUSH)
def set_ios_badge(user):
    # Todo: figure out badge setting for pages
    if user.type == USER_TYPE_PAGE:
        return

    from .notifications_controller import get_total_unread_count

    if user.apns_device:
        badge = get_total_unread_count(user)
        try:
            user.send_apns(alert=None, badge=badge)
            debug_logger.debug("Set APNS badge for %s" % user)
        except APNSError:
            error_logger.warn("Could not set APNS badge for %s" % user, exc_info=True)


def check_push(notification_type):
    return settings.USE_PUSH and notification_type.include_in_push()


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
    error = "user_ids shout be a list <= 1000"
    assert isinstance(user_ids, list) and len(user_ids) <= settings.MAX_BROADCAST_RECIPIENTS, error

    if DEVICE_IOS.value in devices:
        apns_devices = APNSDevice.objects.filter(user__in=user_ids)
        apns_devices.send_message(push_broadcast.message, sound='default')
        debug_logger.debug("Sent Push Broadcast: %s to %d APNS devices" % (push_broadcast.pk, len(apns_devices)))

    if DEVICE_ANDROID.value in devices:
        gcm_devices = GCMDevice.objects.filter(user__in=user_ids)
        extra = {
            'event_name': str(NotificationType.new_notification()),
            'title': "Shoutit",
            'body': push_broadcast.message,

            # Todo: Deprecate old properties
            'notification_type': int(NOTIFICATION_TYPE_BROADCAST),
            'message': push_broadcast.message
        }
        gcm_devices.send_message(None, extra=extra)
        debug_logger.debug("Sent Push Broadcast: %s to %d GCM devices" % (push_broadcast.pk, len(gcm_devices)))


@receiver(post_save, sender=APNSDevice)
def apns_post_save(sender, instance=None, created=False, update_fields=None, **kwargs):
    if created:
        api_version = getattr(instance, 'api_version', api_settings.DEFAULT_VERSION)
        Device.objects.create(user=instance.user, type=DEVICE_IOS, api_version=api_version, push_device=instance)
        debug_logger.debug("Created %s APNSDevice for %s" % (api_version, instance.user))


@receiver(post_save, sender=GCMDevice)
def gcm_post_save(sender, instance=None, created=False, update_fields=None, **kwargs):
    if created:
        api_version = getattr(instance, 'api_version', api_settings.DEFAULT_VERSION)
        Device.objects.create(user=instance.user, type=DEVICE_ANDROID, api_version=api_version, push_device=instance)
        debug_logger.debug("Created %s GCMDevice for %s" % (api_version, instance.user))
