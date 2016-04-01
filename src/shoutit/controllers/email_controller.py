from __future__ import unicode_literals

from django.conf import settings
from django.core.mail.message import EmailMultiAlternatives
from django.template.context import Context
from django.template.loader import get_template
from django.utils.translation import ugettext as _
from django_rq import job

from shoutit.utils import get_google_smtp_connection, error_logger, sss_logger


def send_password_reset_email(user):
    return _send_password_reset_email.delay(user)


@job(settings.RQ_QUEUE_MAIL)
def _send_password_reset_email(user):
    subject = _('Password Reset')
    from_email = settings.DEFAULT_FROM_EMAIL
    context = Context({
        'title': subject,
        'username': user.username,
        'name': user.name if user.name != user.username else '',
        'link': user.password_reset_link
    })
    html_template = get_template('email/passwordrecovery.html')
    html_message = html_template.render(context)
    text_template = get_template('password_recovery_email.txt')
    text_message = text_template.render(context)
    msg = EmailMultiAlternatives(subject, text_message, from_email, [user.email])
    msg.attach_alternative(html_message, "text/html")
    msg.send(True)


def send_verified_email(user):
    return _send_verified_email.delay(user)


@job(settings.RQ_QUEUE_MAIL)
def _send_verified_email(user):
    subject = _('Your email has been verified!')
    from_email = settings.DEFAULT_FROM_EMAIL
    context = Context({
        'title': subject,
        'username': user.username,
        'name': user.name if user.name != user.username else '',
        'link': settings.SITE_LINK,
    })
    html_template = get_template('email/verified.html')
    html_message = html_template.render(context)
    msg = EmailMultiAlternatives(subject, "", from_email, [user.email])
    msg.attach_alternative(html_message, "text/html")
    msg.send(True)


def send_signup_email(user):
    return _send_signup_email.delay(user)


@job(settings.RQ_QUEUE_MAIL)
def _send_signup_email(user):
    subject = _('Welcome to Shoutit!')
    from_email = settings.DEFAULT_FROM_EMAIL
    context = Context({
        'title': subject,
        'username': user.username,
        'name': user.name if user.name != user.username else '',
        'link': user.verification_link,
        'is_activated': user.is_activated
    })
    html_template = get_template('email/registration.html')
    html_message = html_template.render(context)
    msg = EmailMultiAlternatives(subject, "", from_email, [user.email])
    msg.attach_alternative(html_message, "text/html")
    msg.send(True)


def send_verification_email(user):
    return _send_verification_email.delay(user)


@job(settings.RQ_QUEUE_MAIL)
def _send_verification_email(user):
    subject = _('Shoutit - Verify your email')
    from_email = settings.DEFAULT_FROM_EMAIL
    context = Context({
        'title': subject,
        'username': user.username,
        'name': user.name if user.name != user.username else '',
        'link': user.verification_link
    })
    html_template = get_template('email/verification.html')
    html_message = html_template.render(context)
    msg = EmailMultiAlternatives(subject, "", from_email, [user.email])
    msg.attach_alternative(html_message, "text/html")
    msg.send(True)


def send_cl_invitation_email(cl_user):
    return _send_cl_invitation_email.delay(cl_user)


@job(settings.RQ_QUEUE)
def _send_cl_invitation_email(cl_user):
    subject = _('Welcome to Shoutit!')
    from_email = settings.DEFAULT_FROM_EMAIL
    context = Context({
        'shout': cl_user.shout.item.name[:30] + '...',
        'link': 'https://www.shoutit.com/app',
    })
    text_template = get_template('cl_user_invitation_email.txt')
    text_message = text_template.render(context)
    connection = get_google_smtp_connection()
    user = cl_user.user
    email = EmailMultiAlternatives(subject=subject, body=text_message, to=[cl_user.cl_email],
                                   from_email=from_email, connection=connection)
    if email.send(True):
        sss_logger.debug("Sent invitation to cl user: %s" % str(user))
    else:
        error_logger.warn("Failed to send invitation to cl user.", exc_info=True)


def send_db_invitation_email(db_user):
    return _send_db_invitation_email.delay(db_user)


@job(settings.RQ_QUEUE)
def _send_db_invitation_email(db_user):
    subject = _('Welcome to Shoutit!')
    from_email = settings.DEFAULT_FROM_EMAIL
    context = Context({
        'shout': db_user.shout.item.name[:30] + '...',
        'link': 'https://www.shoutit.com/app',
    })
    html_template = get_template('email/db_user_invitation_email.html')
    html_message = html_template.render(context)
    user = db_user.user
    email = EmailMultiAlternatives(subject=subject, to=[user.email], from_email=from_email)
    email.attach_alternative(html_message, "text/html")
    if email.send(True):
        sss_logger.debug("Sent invitation to db user: %s" % str(user))
    else:
        error_logger.warn("Failed to send invitation to db user.", exc_info=True)


def send_template_email_test(template, email, context, use_google_connection=False):
    return _send_template_email_test.delay(template, email, context, use_google_connection)


@job(settings.RQ_QUEUE)
def _send_template_email_test(template, email, context, use_google_connection=False):
    subject = _('Template Test!')
    from_email = settings.DEFAULT_FROM_EMAIL
    context = Context(context)
    html_template = get_template(template)
    html_message = html_template.render(context)
    email = EmailMultiAlternatives(subject=subject, to=[email], from_email=from_email)
    if use_google_connection:
        connection = get_google_smtp_connection()
        email.connection = connection
    email.attach_alternative(html_message, "text/html")
    email.send(True)
