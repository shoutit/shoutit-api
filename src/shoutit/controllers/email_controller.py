from __future__ import unicode_literals

import base64
import json

import sendgrid
from django.conf import settings
from django.utils.translation import ugettext as _
from django_rq import job

from common.utils import date_unix
from shoutit.models import User
from shoutit.utils import debug_logger

SG_WELCOME_TEMPLATE = 'f34f9b3a-92f3-4b11-932e-f0205003897a'
SG_GENERAL_TEMPLATE = '487198e5-5479-4aca-aa6c-f5f36b0a8a61'
SG_API_KEY = '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'
sg = sendgrid.SendGridClient(SG_API_KEY)
sg_api = sendgrid.SendGridAPIClient(apikey=SG_API_KEY)


def prepare_message(user, subject, template, subs=None):
    message = sendgrid.Mail()
    message.add_to(user.email)
    message.set_subject(subject)
    message.set_from(settings.DEFAULT_FROM_EMAIL)
    message.set_html(' ')
    message.add_filter('templates', 'enable', '1')
    message.add_filter('templates', 'template_id', template)
    message.add_substitution('{{site_link}}', settings.SITE_LINK)
    message.add_substitution('{{name}}', user.name)
    if subs:
        for key, val in subs.items():
            message.add_substitution('{{%s}}' % key, val)
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
        'text1': _("Thank you for verifying your email. Your account has been verified and you can now use Shoutit full"
                   " potential."),
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
            'platform': " ".join(map(lambda c: str(c.replace('shoutit-', '')), user.api_client_names)),
            'gender': getattr(ap, 'gender', ''),
        }
        request_body.append(fields)
    try:
        response = sg_api.client.contactdb.recipients.post(request_body=request_body)
        response_data = json.loads(response.response_body)

        # Check added
        if response_data['new_count'] > 0:
            debug_logger.debug("Added %d user(s) to SendGrid Contacts DB" % response_data['new_count'])
        # Check updated
        if response_data['updated_count'] > 0:
            debug_logger.debug("Updated %d user(s) on SendGrid Contacts DB" % response_data['updated_count'])

        # Update added / updated users
        added_emails = map(lambda pr: base64.b64decode(pr), response_data['persisted_recipients'])
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
