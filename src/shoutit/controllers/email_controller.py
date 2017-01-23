from __future__ import unicode_literals

import base64
import json

import sendgrid
from django.conf import settings
from django.utils.encoding import force_text
from django.utils.translation import activate, get_language, gettext_lazy as _
from django_rq import job

from common.constants import USER_TYPE_PAGE
from common.utils import date_unix
from shoutit.models import User
from shoutit.utils import debug_logger, error_logger, url_with_querystring

# Todo (mo): add localized templates and fallback to english ones
SG_WELCOME_TEMPLATE = 'f34f9b3a-92f3-4b11-932e-f0205003897a'
SG_GENERAL_TEMPLATE = '487198e5-5479-4aca-aa6c-f5f36b0a8a61'
SG_API_KEY = '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'
sg = sendgrid.SendGridClient(SG_API_KEY)
sg_api = sendgrid.SendGridAPIClient(apikey=SG_API_KEY)

# Todo: skip sending emails when `EMAIL_ENV` is `file`


def prepare_message(user, subject, template, subs=None):
    lang = get_language()
    activate(user.language)
    message = sendgrid.Mail()
    message.add_to(user.email)
    message.set_subject(force_text(subject))
    message.set_from(settings.DEFAULT_FROM_EMAIL)
    message.set_html(' ')
    message.add_filter('templates', 'enable', '1')
    message.add_filter('templates', 'template_id', template)
    message.add_substitution('{{site_link}}', settings.SITE_LINK)
    message.add_substitution('{{name}}', user.get_full_name())
    if subs:
        for key, val in subs.items():
            message.add_substitution('{{%s}}' % key, force_text(val))
    activate(lang)
    return message


def send_welcome_email(user):
    return _send_welcome_email.delay(user)


@job(settings.RQ_QUEUE_MAIL)
def _send_welcome_email(user):
    subject = _('Welcome!')
    subs = {
        'username': user.username
    }
    if user.is_activated:
        subs.update({
            'text1': "",
            'action': _("Take me to my profile"),
            'link': user.web_url
        })
    else:
        subs.update({
            'text1': _("To get started using Shoutit, please activate your account below"),
            'action': _("Activate your account"),
            'link': user.verification_link
        })
    message = prepare_message(user=user, subject=subject, template=SG_WELCOME_TEMPLATE, subs=subs)
    result = sg.send(message)
    debug_logger.debug("Sent Welcome Email to %s Result: %s" % (user, result))


def send_verification_email(user):
    return _send_verification_email.delay(user)


@job(settings.RQ_QUEUE_MAIL)
def _send_verification_email(user):
    subject = _('Verify your email')
    subs = {
        'text1': _("Your have changed your email therefore your account is not verified. To "
                   "use Shoutit with full potential we need to verify your email."),
        'action': _("Verify it now"),
        'link': user.verification_link
    }
    message = prepare_message(user=user, subject=subject, template=SG_GENERAL_TEMPLATE, subs=subs)
    result = sg.send(message)
    debug_logger.debug("Sent Verification Email to %s Result: %s" % (user, result))


def send_verified_email(user):
    return _send_verified_email.delay(user)


@job(settings.RQ_QUEUE_MAIL)
def _send_verified_email(user):
    subject = _('Your email has been verified!')
    subs = {
        'text1': _("Thank you for verifying your email. Your account has been verified and you can now use Shoutit "
                   "full potential."),
        'action': _("Take me to my profile"),
        'link': user.web_url
    }
    message = prepare_message(user=user, subject=subject, template=SG_GENERAL_TEMPLATE, subs=subs)
    result = sg.send(message)
    debug_logger.debug("Sent Verified Email to %s Result: %s" % (user, result))


def send_password_reset_email(user):
    return _send_password_reset_email.delay(user)


@job(settings.RQ_QUEUE_MAIL)
def _send_password_reset_email(user):
    subject = _('Reset your password')
    subs = {
        'text1': _("You have requested to reset your password. If it wasn't you please let us know as soon as possible."),
        'action': _("Reset my password"),
        'link': user.password_reset_link
    }
    message = prepare_message(user=user, subject=subject, template=SG_GENERAL_TEMPLATE, subs=subs)
    result = sg.send(message)
    debug_logger.debug("Sent Password Reset Email to %s Result: %s" % (user, result))


def send_notification_email(user, notification):
    if not user.email:
        notification_type = notification.get_type_display()
        error_logger.info("Tried to send %s:Notification Email to user who has no email" % notification_type, extra={
            'user': user, 'notification': notification
        })
        return
    # Email the page admins if the notified user is a Page
    if user.type == USER_TYPE_PAGE:
        for admin in user.page.admins.all():
            _send_notification_email.delay(admin, notification, emailed_for=user)
        return
    else:
        return _send_notification_email.delay(user, notification)


@job(settings.RQ_QUEUE_MAIL)
def _send_notification_email(user, notification, emailed_for=None):
    from shoutit.controllers import pusher_controller

    # Do nothing if the user is in app (subscribed to Pusher)
    if pusher_controller.check_pusher(user):
        return

    display = notification.display()
    subject = display['title']
    if emailed_for:
        intro = _("Your page '%(page)s' has a new notification") % {'page': emailed_for.name}
        auth_token = emailed_for.get_valid_auth_token(page_admin_user=user)
    else:
        intro = _("You have a new notification")
        auth_token = user.get_valid_auth_token()
    link = url_with_querystring(notification.web_url, auth_token=auth_token.pk)
    subs = {
        'text1':
            """
            %(intro)s
            <blockquote style="font-weight:bold;background-color:#EEEEEE;padding:10px;border-radius:5px;">%(text)s</blockquote>
            <p style="font-style:italic;color:#888888;margin-top:50px;">%(note)s</p>
            """ % {'intro': force_text(intro), 'text': force_text(display['text']) or '', 'note': force_text(display.get('note')) or ''},
        'action': display['action'],
        'link': link
    }
    message = prepare_message(user=user, subject=subject, template=SG_GENERAL_TEMPLATE, subs=subs)
    result = sg.send(message)
    debug_logger.debug("Sent Notification Email to %s Result: %s" % (user, result))


def subscribe_users_to_mailing_list(users=None, user_ids=None, raise_errors=True):
    if settings.EMAIL_ENV == 'file':
        return
    return _subscribe_users_to_mailing_list.delay(users=users, user_ids=user_ids, raise_errors=raise_errors)


@job(settings.RQ_QUEUE_MAIL)
def _subscribe_users_to_mailing_list(users=None, user_ids=None, raise_errors=True):
    if users is None:
        users = User.objects.filter(id__in=user_ids)
    request_body = []
    for user in users:
        ap = user.ap
        fields = {
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'is_active': 'true' if user.is_active else 'false',
            'is_activated': 'true' if user.is_activated else 'false',
            'type': user.v3_type_name,
            'username': user.username,
            'date_joined': date_unix(user.date_joined),
            'last_login': date_unix(user.last_login) if user.last_login else 0,
            'country': ap.country,
            'image': ap.image,
            'platform': " ".join([c.replace('shoutit-', '') for c in user.api_client_names]),
            'gender': getattr(ap, 'gender', ''),
        }
        request_body.append(fields)
    try:
        response = sg_api.client.contactdb.recipients.post(request_body=request_body)
        response_data = json.loads(response.response_body.decode())

        # Check added
        if response_data['new_count'] > 0:
            debug_logger.debug("Added %d user(s) to SendGrid Contacts DB" % response_data['new_count'])
        # Check updated
        if response_data['updated_count'] > 0:
            debug_logger.debug("Updated %d user(s) on SendGrid Contacts DB" % response_data['updated_count'])

        # Update added / updated users
        added_emails = [base64.b64decode(pr) for pr in response_data['persisted_recipients']]
        User.objects.filter(email__in=added_emails).update(on_mailing_list=True)

        # Errors
        if response_data['error_count'] > 0:
            debug_logger.warning("Error adding/updating %d user(s) to SendGrid contacts db" % response_data['error_count'])
            debug_logger.warning(response_data['errors'])
            raise ValueError(response_data['errors'])
    except Exception as e:
        debug_logger.warning("Error adding/updating %d users to SendGrid: %s" % (len(users), str(e)))
        if raise_errors:
            raise
