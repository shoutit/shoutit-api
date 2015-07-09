from __future__ import unicode_literals
import uuid
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.http import HttpRequest
from django.utils.translation import ugettext as _
from django.db.models.query_utils import Q
from push_notifications.apns import APNSError
from push_notifications.gcm import GCMError
from django_rq import job
from pusher import Pusher
import requests
from rest_framework.request import Request
from common.constants import (NOTIFICATION_TYPE_LISTEN, NOTIFICATION_TYPE_MESSAGE,
                              NOTIFICATION_TYPE_EXP_POSTED, NOTIFICATION_TYPE_EXP_SHARED,
                              NOTIFICATION_TYPE_COMMENT)
from shoutit.api.versioning import ShoutitNamespaceVersioning
from shoutit.controllers import email_controller
from shoutit.models import Notification, DBCLConversation
from shoutit.utils import get_google_smtp_connection, error_logger, debug_logger, sss_logger
from shoutit_pusher.models import PusherChannel
from shoutit_pusher.utils import pusher


class NotifySSSException(Exception):
    pass


def mark_all_as_read(user):
    Notification.objects.filter(is_read=False, ToUser=user).update(is_read=True)


def mark_notifications_as_read_by_ids(notification_ids):
    Notification.objects.filter(id__in=notification_ids).update(is_read=True)


@job(settings.RQ_QUEUE)
def notify_user(user, notification_type, from_user=None, attached_object=None, request=None):
    from shoutit.api.v2 import serializers
    if not request:
        # todo: create general fake request
        django_request = HttpRequest()
        django_request.META['SERVER_NAME'] = 'api.shoutit.com'
        django_request.META['SERVER_PORT'] = '80'
        request = Request(django_request)
        request.version = 'v2'
        request.versioning_scheme = ShoutitNamespaceVersioning()

    # set the request.user to the notified user as if he was asking for it.
    request.user = user

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

    if check_pusher(user, notification_type, attached_object):
        send_pusher(user, notification_type, attached_object_dict)
    elif not settings.DEBUG or settings.FORCE_PUSH:
        send_push(user, attached_object_dict, message, notification_type)

    if notification_type == NOTIFICATION_TYPE_MESSAGE and from_user \
            and not getattr(attached_object.conversation.attached_object, 'is_disabled', False) \
            and (not settings.DEBUG or settings.FORCE_SSS_NOTIFY) and attached_object.text:
        send_sss(user, attached_object, notification_type, from_user)


def check_pusher(user, notification_type, attached_object):
    return PusherChannel.objects.filter(name='presence-u-%s' % user.pk).exists()
    # todo: check if we really want to send new messages on chat channel
    # if notification_type == NOTIFICATION_TYPE_MESSAGE:
    #     return PusherChannel.objects.filter(name='presence-c-%s' % attached_object.conversation.pk).exists()
    # else:
    #     return PusherChannel.objects.filter(name='presence-u-%s' % user.pk).exists()


def send_pusher(user, notification_type, attached_object_dict):
    pusher.trigger('presence-u-%s' % user.pk, str(notification_type), attached_object_dict)
    # todo: check if we really want to send new messages on chat channel
    # if notification_type == NOTIFICATION_TYPE_MESSAGE:
    #     pusher.trigger('presence-c-%s' % attached_object_dict.get('conversation_id'), 'new_message', attached_object_dict)
    # elif notification_type == NOTIFICATION_TYPE_LISTEN:
    #     pusher.trigger('presence-u-%s' % user.pk, 'new_listen')


def send_push(user, attached_object_dict, message, notification_type):
    if user.apns_device:
        try:
            user.apns_device.send_message(
                message, sound='default', badge=get_user_notifications_count(user), extra={
                    'notification_type': int(notification_type),
                    'object': attached_object_dict
                })
            debug_logger.debug("Sent apns push to %s." % user)
        except APNSError, e:
            error_logger.warn("Could not send apns push.", extra={
                'user': user.username,
                'APNSError': str(e)
            })

    if user.gcm_device:
        try:
            user.gcm_device.send_message(message, extra={
                'notification_type': int(notification_type),
                'object': attached_object_dict
            })
            debug_logger.debug("Sent gcm push to %s." % user)
        except GCMError, e:
            error_logger.warn("Could not send gcm push.", extra={
                'user': user.username,
                'GCMError': str(e)
            })


def send_sss(user, attached_object, notification_type, from_user):
    if user.db_user:
        if not user.email:
            notify_db_user.delay(user.db_user, from_user, attached_object)
        else:
            notify_db_user.dealy(user.db_user, from_user, attached_object)
            # todo: !
            # email_controller.email_db_user(user.db_user, from_user, attached_object)
    elif user.dbz2_user:
        notify_dbz2_user.delay(user.dbz2_user, from_user, attached_object)
    elif user.cl_user:
        notify_cl_user2.delay(user.cl_user, from_user, attached_object)


def get_dbz_base_url(db_link):
    import urlparse
    parts = urlparse.urlparse(db_link)
    return parts.scheme + '://' + parts.netloc


@job(settings.RQ_QUEUE)
def notify_db_user(db_user, from_user, message):
    from antigate import AntiGate
    import re

    base_url = get_dbz_base_url(db_user.db_link)
    reply_url = db_user.db_link + '?reply'
    reply_response = requests.get(reply_url)
    if reply_response.status_code != 200:
        error_logger.warn("Deleted dbz ad.", extra={
            'db_link': db_user.db_link,
            'conversation': message.conversation.pk
        })
        return
    reply_html = reply_response.content.decode('utf-8')
    captcha_url = base_url + re.search('src="(.*?captcha.*?)"', reply_html).groups()[0]
    captcha_img = requests.get(captcha_url)
    gate = AntiGate(key=settings.ANTI_KEY, captcha_file=captcha_img.content, binary=True)
    captcha_code = str(gate)
    captcha_hash = re.search('captcha/image_mobile/(.*?)/', captcha_url).groups()[0]

    ref = uuid.uuid4().hex
    in_email = ref + '@dbz-reply.com'
    sms_code = ref[-6:].upper()
    DBCLConversation.objects.create(in_email=in_email, from_user=from_user, to_user=db_user.user,
                                    shout=message.conversation.about, ref=ref, sms_code=sms_code)
    form_data = {
        'form_type': 'contact',
        'email': in_email,
        'name': from_user.name,
        'telephone': '.',
        'message': message.text,
        'captcha_0': captcha_hash,
        'captcha_1': captcha_code
    }
    res = requests.post(reply_url, form_data)
    db_res_content = res.content.decode('utf-8').strip()
    if 'Sent Succ' in db_res_content:
        sss_logger.debug("Sent message to dbz user about his ad on: %s" % db_user.db_link)
    else:
        msg = "Error sending message to dbz user: " + db_user.db_link + '\n' + db_res_content
        sss_logger.warn(msg)
        raise NotifySSSException("Error sending message to dbz user")


@job(settings.RQ_QUEUE)
def notify_dbz2_user(dbz2_user, from_user, message):
    from antigate import AntiGate
    from fake_useragent import UserAgent
    import re

    ad = requests.head(dbz2_user.db_link, allow_redirects=False)
    if ad.status_code != 200:
        error_logger.warn("Deleted dbz2 ad.", extra={
            'db_link': dbz2_user.db_link,
            'conversation': message.conversation.pk
        })
        return

    base_url = get_dbz_base_url(dbz2_user.db_link)
    reply_url = dbz2_user.db_link.replace('/show/', '/reply/')

    client = requests.session()
    headers = {
        'User-Agent': UserAgent().random,
        'X-Requested-With': 'XMLHttpRequest',
        'Referer': reply_url
    }
    reply_html = client.get(reply_url, headers=headers).content
    csrftoken = client.cookies.get('csrftoken')

    captcha_url = base_url + re.search('src="(.*?captcha.*?)"', reply_html).groups()[0]
    captcha_img = requests.get(captcha_url)
    gate = AntiGate(key=settings.ANTI_KEY, captcha_file=captcha_img.content, binary=True)
    captcha_code = str(gate)
    captcha_hash = re.search('captcha/image/(.*?)/', captcha_url).groups()[0]

    ref = uuid.uuid4().hex
    in_email = ref + '@dbz-reply.com'
    sms_code = ref[-6:].upper()
    DBCLConversation.objects.create(in_email=in_email, from_user=from_user, to_user=dbz2_user.user,
                                    shout=message.conversation.about, ref=ref, sms_code=sms_code)
    form_data = {
        'is_ajax': '1',
        'csrfmiddlewaretoken': csrftoken,
        'email': in_email,
        'name': from_user.name,
        'mobile_number': '',
        'message': message.text,
        'captcha_0': captcha_hash,
        'captcha_1': captcha_code
    }
    res = client.post(reply_url, data=form_data, headers=headers)
    db_res_content = res.content.decode('utf-8').strip()
    if 'success' in db_res_content:
        sss_logger.debug("Sent message to dbz2 user about his ad on: %s" % dbz2_user.db_link)
    else:
        msg = "Error sending message to dbz2 user: " + dbz2_user.db_link
        if '<!doctype html>' in db_res_content:
            db_res_content = 'Truncated full html page response.'
        msg += '\n' + db_res_content
        sss_logger.warn(msg)
        raise NotifySSSException("Error sending message to dbz2 user")


@job(settings.RQ_QUEUE)
def notify_cl_user2(cl_user, from_user, message):
    shout = message.conversation.about
    subject = shout.item.name
    ref = "%s-%s" % (from_user.username, shout.pk)
    in_email = ref + '@dbz-reply.com'
    try:
        DBCLConversation.objects.get(in_email=in_email)
    except DBCLConversation.DoesNotExist:
        DBCLConversation.objects.create(in_email=in_email, from_user=from_user, to_user=cl_user.user,
                                        shout=message.conversation.about, ref=ref)
    reply_to = "%s <%s>" % (from_user.name, in_email)
    connection = get_google_smtp_connection()
    email = EmailMultiAlternatives(subject=subject, body=message.text, to=[cl_user.cl_email],
                                   from_email=reply_to, reply_to=[reply_to], connection=connection)
    if email.send(True) == 1:
        debug_logger.debug("Sent message to cl user about his ad id: %s" % cl_user.cl_ad_id)
    else:
        error_logger.warn("Error sending message to cl user.", extra={
            'cl_email': cl_user.cl_email
        })


def notify_cl_user(cl_user, from_user, message):
    shout = message.conversation.about
    subject = shout.item.name
    ref = "%s-%s" % (cl_user.cl_ad_id, from_user.pk)
    try:
        DBCLConversation.objects.get(ref=ref)
    except DBCLConversation.DoesNotExist:
        dbcl_conversation = DBCLConversation(
            ref=ref, from_user=from_user, to_user=cl_user.user, shout=shout)
        dbcl_conversation.save()

    email = EmailMultiAlternatives(
        subject, "", "%s <%s>" % (from_user.name, settings.EMAIL_HOST_USER), [cl_user.cl_email])
    html_message = """
    <p>%s</p>
    <br>
    <br>
    <p style="max-height:1px;min-height:1px;font-size:0;display:none;color:#fffffe">{ref:%s}</p>
    """ % (message.text, ref)
    email.attach_alternative(html_message, "text/html")
    email.send(True)


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
