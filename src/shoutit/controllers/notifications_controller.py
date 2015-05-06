from __future__ import unicode_literals
import uuid
from django.conf import settings
from django.utils.translation import ugettext as _
from django.db.models.query_utils import Q
from push_notifications.apns import APNSError
from push_notifications.gcm import GCMError
from django_rq import job
import requests
from common.constants import (NOTIFICATION_TYPE_LISTEN, NOTIFICATION_TYPE_MESSAGE,
                              NOTIFICATION_TYPE_EXP_POSTED, NOTIFICATION_TYPE_EXP_SHARED,
                              NOTIFICATION_TYPE_COMMENT)
from shoutit.controllers import email_controller
from shoutit.models import Notification, DBCLConversation
import logging
logger = logging.getLogger('shoutit.debug')
error_logger = logging.getLogger('shoutit.error')


def mark_all_as_read(user):
    Notification.objects.filter(is_read=False, ToUser=user).update(is_read=True)


def mark_notifications_as_read_by_ids(notification_ids):
    Notification.objects.filter(id__in=notification_ids).update(is_read=True)


@job(settings.RQ_QUEUE)
def notify_user(user, notification_type, from_user=None, attached_object=None, request=None):
    from shoutit.api.v2 import serializers

    notification = Notification(ToUser=user, type=notification_type, FromUser=from_user,
                                attached_object=attached_object)
    notification.save()

    if notification_type == NOTIFICATION_TYPE_LISTEN:
        message = _("You got a new listen")
        attached_object_dict = serializers.UserSerializer(attached_object,
                                                          context={'request': request}).data
    elif notification_type == NOTIFICATION_TYPE_MESSAGE:
        message = _("You got a new message")
        attached_object_dict = serializers.MessageSerializer(attached_object,
                                                             context={'request': request}).data
    else:
        message = None
        attached_object_dict = {}

    if user.apns_device:
        try:
            user.apns_device.send_message(
                message, sound='default', badge=get_user_notifications_count(user), extra={
                    'notification_type': int(notification_type),
                    'object': attached_object_dict
                })
            logger.debug("Sent apns push to %s." % user)
        except APNSError, e:
            error_logger.warn("Could not send apns push to user %s." % user.username)
            error_logger.warn("APNSError:", e)

    if user.gcm_device:
        try:
            user.gcm_device.send_message(message, extra={
                'notification_type': int(notification_type),
                'object': attached_object_dict
            })
            logger.debug("Sent gcm push to %s." % user)
        except GCMError, e:
            error_logger.warn("Could not send gcm push to user %s." % user.username)
            error_logger.warn("GCMError:", e)

    if notification_type == NOTIFICATION_TYPE_MESSAGE:
        if user.db_user:
            if not user.email:
                notify_db_user(user.db_user, from_user, attached_object)
            else:
                notify_db_user(user.db_user, from_user, attached_object)
                # todo: !
                # email_controller.email_db_user(user.db_user, from_user, attached_object)


def notify_db_user(db_user, from_user, message):
    from pyquery import PyQuery as pq
    import urlparse
    from antigate import AntiGate
    url_parts = urlparse.urlparse(db_user.db_link)
    reply_url = db_user.db_link + '?reply'
    d = pq(url=reply_url)
    captcha_url = "%s://%s%s" % (url_parts[0], url_parts[1], d('img.captcha')[0].attrib['src'])
    captcha_img = requests.get(captcha_url)
    gate = AntiGate(key=settings.ANTI_KEY, captcha_file=captcha_img.content, binary=True)
    captcha = str(gate)
    ref = uuid.uuid4().hex
    in_email = ref + '@dbz-reply.com'
    DBCLConversation.objects.create(in_email=in_email, from_user=from_user, to_user=db_user.user,
                                    shout=message.conversation.about, ref=ref)
    form_data = {
        'form_type': 'contact',
        'email': in_email,
        'name': from_user.name,
        'telephone': '.',
        'message': message.text,
        'captcha_0': d('#id_captcha_0').attr('value'),
        'captcha_1': captcha
    }
    res = requests.post(reply_url, form_data)
    db_res_content = res.content.decode('utf-8')
    if 'error' not in res.content:
        logger.debug("Sent message to db user about his ad on: %s" % db_user.db_link)
    else:
        d = pq(db_res_content)
        error_logger.error("Error sending message to db user.", extra={'db_response': d('#container').text()})


def notify_user_of_listen(user, listener, request=None):
    notify_user.delay(user, NOTIFICATION_TYPE_LISTEN, listener, listener, request)


def notify_user_of_message(user, message, request=None):
    notify_user.delay(user, NOTIFICATION_TYPE_MESSAGE, message.user, message, request)


def notify_business_of_exp_posted(business, exp):
    notify_user.delay(business, NOTIFICATION_TYPE_EXP_POSTED, from_user=exp.user,
                      attached_object=exp)


def notify_user_of_exp_shared(user, shared_exp):
    notify_user.delay(user, NOTIFICATION_TYPE_EXP_SHARED, from_user=shared_exp.user,
                      attached_object=shared_exp)


def notify_users_of_comment(users, comment):
    for user in users:
        notify_user.delay(user, NOTIFICATION_TYPE_COMMENT, from_user=comment.user,
                          attached_object=comment)


def get_user_notifications_count(user):
    return Notification.objects.filter(is_read=False, ToUser=user).count()


def get_user_notifications_without_messages_count(user):
    return Notification.objects.filter(
        Q(is_read=False) & Q(ToUser=user) & ~Q(type=NOTIFICATION_TYPE_MESSAGE)).count()
