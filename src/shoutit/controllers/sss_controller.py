from __future__ import unicode_literals

import re
import uuid

import requests
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.core.mail import get_connection
from django_rq import job

from common.constants import NOTIFICATION_TYPE_MESSAGE
from ..models import DBCLConversation
from ..utils import error_logger, debug_logger, sss_logger, send_nexmo_sms


class NotifySSSException(Exception):
    pass


def get_google_smtp_connection():
    return get_connection(**settings.EMAIL_BACKENDS['google'])


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
        dbcl_conversation = DBCLConversation(from_user=from_user, to_user=sss_user, shout=shout, ref=ref,
                                             sms_code=sms_code)
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
    # captcha_img = requests.get(captcha_url)
    # gate = AntiGate(key=settings.ANTI_KEY, captcha_file=captcha_img.content, binary=True)
    captcha_code = str("")
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
    conversation = message.conversation
    shout = conversation.about

    ad = requests.head(dbz2_user.db_link, allow_redirects=False)
    if ad.status_code != 200:
        return

    base_url = get_dbz_base_url(dbz2_user.db_link)
    reply_url = dbz2_user.db_link.replace('/show/', '/reply/')

    client = requests.session()
    headers = {
        # 'User-Agent': UserAgent().random,
        'X-Requested-With': 'XMLHttpRequest',
        'Referer': reply_url
    }
    reply_html = client.get(reply_url, headers=headers).content
    csrftoken = client.cookies.get('csrftoken')

    captcha_url = base_url + re.search('src="(.*?captcha.*?)"', reply_html).groups()[0]
    # captcha_img = requests.get(captcha_url)
    # gate = AntiGate(key=settings.ANTI_KEY, captcha_file=captcha_img.content, binary=True)
    captcha_code = str("")
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
