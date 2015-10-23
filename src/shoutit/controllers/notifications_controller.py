from __future__ import unicode_literals
import uuid
import requests
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.http import HttpRequest
from django.utils.translation import ugettext as _
from django.db.models.query_utils import Q
from push_notifications.apns import APNSError
from push_notifications.gcm import GCMError
from push_notifications.models import APNSDevice, GCMDevice
from django_rq import job
from rest_framework.request import Request
from common.constants import (NOTIFICATION_TYPE_LISTEN, NOTIFICATION_TYPE_MESSAGE, NOTIFICATION_TYPE_EXP_POSTED,
                              NOTIFICATION_TYPE_EXP_SHARED, NOTIFICATION_TYPE_COMMENT, DEVICE_ANDROID, DEVICE_IOS,
                              NOTIFICATION_TYPE_BROADCAST)
from shoutit.api.versioning import ShoutitNamespaceVersioning
from shoutit.models import Notification, DBCLConversation, Message, User, PushBroadcast
from shoutit.utils import get_google_smtp_connection, error_logger, debug_logger, sss_logger, send_nexmo_sms
from shoutit_pusher.models import PusherChannel
from shoutit_pusher.utils import pusher
from antigate import AntiGate
import re
from copy import deepcopy


class NotifySSSException(Exception):
    pass


def mark_all_as_read(user):
    Notification.objects.filter(is_read=False, ToUser=user).update(is_read=True)


def mark_notifications_as_read_by_ids(notification_ids):
    Notification.objects.filter(id__in=notification_ids).update(is_read=True)


def serialize_attached_object(attached_object, user, request):
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

    if isinstance(attached_object, User):
        attached_object_dict = serializers.UserSerializer(attached_object, context={'request': request}).data
    elif isinstance(attached_object, Message):
        attached_object_dict = serializers.MessageSerializer(attached_object, context={'request': request}).data
    else:
        attached_object_dict = {}
    return attached_object_dict


def check_pusher(user):
    return PusherChannel.objects.filter(name='presence-u-%s' % user.pk).exists()


def check_push():
    return (not settings.DEBUG) or settings.FORCE_PUSH


def check_sss(user, notification_type, attached_object, from_user):
    if notification_type != NOTIFICATION_TYPE_MESSAGE:
        return False
    if not user.sss_user or user.sss_user.converted_at:
        return False
    disabled_shout = getattr(attached_object.conversation.attached_object, 'is_disabled', False)
    text = getattr(attached_object, 'text')
    force_sss = not settings.DEBUG or settings.FORCE_SSS_NOTIFY
    return not disabled_shout and from_user and text and force_sss


def get_dbz_base_url(db_link):
    import urlparse
    parts = urlparse.urlparse(db_link)
    return parts.scheme + '://' + parts.netloc


@job(settings.RQ_QUEUE)
def notify_user(user, notification_type, from_user=None, attached_object=None, request=None):
    # send notification to pusher
    attached_object_dict = serialize_attached_object(attached_object, user, request)
    send_pusher.delay(user, notification_type, attached_object_dict)

    # create notification object
    Notification.create(ToUser=user, type=notification_type, FromUser=from_user, attached_object=attached_object)

    # send appropriate notification
    if check_sss(user, notification_type, attached_object, from_user):
        send_sss(user, attached_object, notification_type, from_user)
    elif check_push() and not check_pusher(user):
        send_push.delay(user, notification_type, attached_object_dict)


@job(settings.RQ_QUEUE_PUSHER)
def send_pusher(user, notification_type, attached_object_dict):
    pusher.trigger('presence-u-%s' % user.pk, str(notification_type), attached_object_dict)


@job(settings.RQ_QUEUE_PUSHER)
def send_pusher_message(message, request=None):
    message_dict = serialize_attached_object(message, message.user, request)
    pusher.trigger('presence-c-%s' % message.conversation.pk, str(NOTIFICATION_TYPE_MESSAGE), message_dict)


@job(settings.RQ_QUEUE_PUSH)
def send_push(user, notification_type, attached_object_dict):
    if notification_type == NOTIFICATION_TYPE_LISTEN:
        message = _("You got a new listen")
    elif notification_type == NOTIFICATION_TYPE_MESSAGE:
        message = _("You got a new message")
    else:
        message = None

    if user.apns_device:
        try:
            user.apns_device.send_message(
                message, sound='default', badge=get_user_notifications_count(user), extra={
                    'notification_type': int(notification_type),
                    'object': attached_object_dict
                })
            debug_logger.debug("Sent apns push to %s." % user)
        except APNSError:
            error_logger.warn("Could not send apns push.", exc_info=True)

    if user.gcm_device:
        try:
            user.gcm_device.send_message(message, extra={
                'notification_type': int(notification_type),
                'object': attached_object_dict
            })
            debug_logger.debug("Sent gcm push to %s." % user)
        except GCMError:
            error_logger.warn("Could not send gcm push.", exc_info=True)


@job(settings.RQ_QUEUE_SSS)
def send_sss(user, attached_object, notification_type, from_user):
    if user.db_user:
        if not user.email:
            notify_db_user.delay(user.db_user, from_user, attached_object)
        else:
            notify_db_user.delay(user.db_user, from_user, attached_object)
            # todo: !
            # email_controller.email_db_user(user.db_user, from_user, attached_object)
    elif user.dbz2_user:
        if user.profile.mobile:
            sms_sss_user.delay(user, from_user, attached_object)
        else:
            notify_dbz2_user.delay(user.dbz2_user, from_user, attached_object)
    elif user.cl_user:
        notify_cl_user2.delay(user.cl_user, from_user, attached_object)


@job(settings.RQ_QUEUE_SSS)
def sms_sss_user(sss_user, from_user, message, sms_anyway=False):
    shout = message.conversation.about

    # check for existing dbcl conversation. do not create new one.
    try:
        dbcl_conversation = DBCLConversation.objects.get(from_user=from_user, to_user=sss_user, shout=shout)
        if not sms_anyway:
            return
    except DBCLConversation.DoesNotExist:
        # create dbcl conversation
        ref = uuid.uuid4().hex
        sms_code = ref[-6:]
        dbcl_conversation = DBCLConversation(from_user=from_user, to_user=sss_user, shout=shout, ref=ref, sms_code=sms_code)
        dbcl_conversation.save()
    except DBCLConversation.MultipleObjectsReturned:
        dbcl_conversation = DBCLConversation.objects.filter(from_user=from_user, to_user=sss_user, shout=shout)[0]

    # send the sms
    text = message.text or ''
    to = sss_user.profile.mobile
    body = "you got a message about '%s...'\n\n%s\n\nreply on\nshoutit.com/%s"
    body %= (shout.item.name[:20], text[:50], dbcl_conversation.sms_code)
    send_nexmo_sms(to, body, len_restriction=False)


@job(settings.RQ_QUEUE_SSS)
def notify_db_user(db_user, from_user, message):
    conversation = message.conversation
    shout = conversation.about

    base_url = get_dbz_base_url(db_user.db_link)
    reply_url = db_user.db_link + '?reply'
    reply_response = requests.get(reply_url)
    if reply_response.status_code != 200:
        return
    reply_html = reply_response.content.decode('utf-8')
    captcha_url = base_url + re.search('src="(.*?captcha.*?)"', reply_html).groups()[0]
    captcha_img = requests.get(captcha_url)
    gate = AntiGate(key=settings.ANTI_KEY, captcha_file=captcha_img.content, binary=True)
    captcha_code = str(gate)
    captcha_hash = re.search('captcha/image_mobile/(.*?)/', captcha_url).groups()[0]

    ref = uuid.uuid4().hex
    in_email = ref + '@dbz-reply.com'
    sms_code = ref[-6:]
    DBCLConversation.objects.create(in_email=in_email, from_user=from_user, to_user=db_user.user,
                                    shout=shout, ref=ref, sms_code=sms_code)
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


@job(settings.RQ_QUEUE_SSS)
def notify_dbz2_user(dbz2_user, from_user, message):
    from fake_useragent import UserAgent
    conversation = message.conversation
    shout = conversation.about

    ad = requests.head(dbz2_user.db_link, allow_redirects=False)
    if ad.status_code != 200:
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
    sms_code = ref[-6:]
    DBCLConversation.objects.create(in_email=in_email, from_user=from_user, to_user=dbz2_user.user,
                                    shout=shout, ref=ref, sms_code=sms_code)
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


@job(settings.RQ_QUEUE_SSS)
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
    cl_email = cl_user.cl_email
    email = EmailMultiAlternatives(subject=subject, body=message.text, to=[cl_email],
                                   from_email=reply_to, reply_to=[reply_to], connection=connection)
    if email.send(True) == 1:
        debug_logger.debug("Sent message to cl user about his ad id: %s" % cl_user.cl_ad_id)
    else:
        error_logger.warn("Error sending message to cl user.", exc_info=True)


def notify_user_of_listen(user, listener, request=None):
    listener = deepcopy(listener)
    notify_user.delay(user, NOTIFICATION_TYPE_LISTEN, listener, listener, deepcopy(request))


def notify_user_of_message(user, message, request=None):
    notify_user.delay(user, NOTIFICATION_TYPE_MESSAGE, deepcopy(message.user), message, deepcopy(request))


def notify_business_of_exp_posted(business, exp):
    notify_user.delay(business, NOTIFICATION_TYPE_EXP_POSTED, from_user=exp.user, attached_object=exp)


def notify_user_of_exp_shared(user, shared_exp):
    notify_user.delay(user, NOTIFICATION_TYPE_EXP_SHARED, from_user=shared_exp.user, attached_object=shared_exp)


def notify_users_of_comment(users, comment):
    for user in users:
        notify_user.delay(user, NOTIFICATION_TYPE_COMMENT, from_user=comment.user, attached_object=comment)


def get_user_notifications_count(user):
    return Notification.objects.filter(is_read=False, ToUser=user).count()


def get_user_notifications_without_messages_count(user):
    return Notification.objects.filter(Q(is_read=False) & Q(ToUser=user) & ~Q(type=NOTIFICATION_TYPE_MESSAGE)).count()


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
    assert isinstance(user_ids, list) and len(user_ids) <= settings.MAX_BROADCAST_RECIPIENTS, "user_ids shout be a list <= 1000"

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
