from __future__ import unicode_literals
from django.core.mail.message import EmailMultiAlternatives
from django.template.context import Context
from django.template.loader import get_template
from django.utils.translation import ugettext as _
from django.core.mail import get_connection
from django.conf import settings
from django_rq import job
from common import constants
from shoutit.utils import get_google_smtp_connection, error_logger, sss_logger


def SendEmail(email, variables, html_template, text_template):
    subject = _('[ShoutIt] Welcome to ShoutIt!')
    from_email = settings.DEFAULT_FROM_EMAIL
    to = email

    html_template = get_template(html_template)
    html_context = Context(variables)
    html_message = html_template.render(html_context)

    text_template = get_template(text_template)
    text_context = Context(variables)
    text_message = text_template.render(text_context)

    msg = EmailMultiAlternatives(subject, text_message, from_email, [to])
    msg.attach_alternative(html_message, "text/html")

    msg.send(True)


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


def SendListenEmail(follower, followed):
    subject = _('[ShoutIt] %(name)s has started listening to your shouts') % {'name': follower.name}
    link = '%s%s' % (settings.SITE_LINK, constants.PROFILE_URL % follower.username)
    from_email = settings.DEFAULT_FROM_EMAIL
    to = followed.email

    html_template = get_template('followship_email.html')
    html_context = Context({
        'followed': followed.name,
        'follower': follower.name,
        'link': link
    })
    html_message = html_template.render(html_context)

    text_template = get_template('followship_email.txt')
    text_context = Context({
        'followed': followed.name,
        'follower': follower.name,
        'link': link
    })
    text_message = text_template.render(text_context)

    msg = EmailMultiAlternatives(subject, text_message, from_email, [to])
    msg.attach_alternative(html_message, "text/html")
    msg.send(True)


def SendExpiryNotificationEmail(user, shout):
    subject = _('[ShoutIt] your shout is about to expire! reshout it now.')
    title = shout.item.name
    link = '%s%s' % (settings.SITE_LINK, constants.SHOUT_URL % shout.pk)
    from_email = settings.DEFAULT_FROM_EMAIL
    to = user.email

    html_template = get_template('expiry_email.html')
    html_context = Context({
        'username': user.first_name + ' ' + user.last_name,
        'title': title,
        'link': link
    })
    html_message = html_template.render(html_context)

    text_template = get_template('expiry_email.txt')
    text_context = Context({
        'username': user.first_name + ' ' + user.last_name,
        'title': title,
        'link': link
    })
    text_message = text_template.render(text_context)

    msg = EmailMultiAlternatives(subject, text_message, from_email, [to])
    msg.attach_alternative(html_message, "text/html")

    msg.send(True)


def SendBuyOfferEmail(shout, buyer):
    subject = u'[Shoutit] %s offered to buy your %s' % (buyer.username, shout.name)
    shout_link = '%s%s' % (settings.SITE_LINK, constants.SHOUT_URL % shout.pk)
    buyer_link = '%s%s' % (settings.SITE_LINK, constants.PROFILE_URL % buyer.username)
    mute_link = '%s%s' % (settings.SITE_LINK, constants.MUTE_URL % shout.pk)
    from_email = settings.DEFAULT_FROM_EMAIL
    to = shout.user.email

    html_template = get_template('buy_offer_email.html')
    html_context = Context({
        'username': shout.user.username,
        'buyer': buyer.username,
        'shout_link': shout_link,
        'buyer_link': buyer_link,
        'mute_link': mute_link,
        'buyer_email': buyer.email
    })
    html_message = html_template.render(html_context)

    text_template = get_template('buy_offer_email.txt')
    text_context = Context({
        'username': shout.user.username,
        'buyer': buyer.username,
        'shout_link': shout_link,
        'buyer_link': buyer_link,
        'mute_link': mute_link,
        'buyer_email': buyer.email
    })
    text_message = text_template.render(text_context)

    msg = EmailMultiAlternatives(subject, text_message, from_email, [to],
                                 headers={'Reply-To': buyer.email})
    msg.attach_alternative(html_message, "text/html")

    msg.send(True)


def SendSellOfferEmail(shout, seller):
    subject = u'[ShoutIt] %s has %s and willing to sell it to you' % (seller.username, shout.name)
    shout_link = '%s%s' % (settings.SITE_LINK, constants.SHOUT_URL % shout.pk)
    seller_link = '%s%s' % (settings.SITE_LINK, constants.PROFILE_URL % seller.username)
    mute_link = '%s%s' % (settings.SITE_LINK, constants.MUTE_URL % shout.pk)
    from_email = settings.DEFAULT_FROM_EMAIL
    to = shout.user.email

    html_template = get_template('sell_offer_email.html')
    html_context = Context({
        'username': shout.user.username,
        'buyer': seller.username,
        'shout_link': shout_link,
        'seller_link': seller_link,
        'mute_link': mute_link,
        'seller_email': seller.email
    })
    html_message = html_template.render(html_context)

    text_template = get_template('sell_offer_email.txt')
    text_context = Context({
        'username': shout.user.username,
        'buyer': seller.username,
        'shout_link': shout_link,
        'seller_link': seller_link,
        'mute_link': mute_link,
        'seller_email': seller.email
    })
    text_message = text_template.render(text_context)

    msg = EmailMultiAlternatives(subject, text_message, from_email, [to],
                                 headers={'Reply-To': seller.email})
    msg.attach_alternative(html_message, "text/html")
    msg.send()


def send_message_email(message):
    to_user = message.ToUser
    from_user = message.FromUser
    shout = message.Conversation.AboutPost
    message_text = message.text

    to_name = to_user.name
    to_email = to_user.email

    from_name = from_user.name
    from_email = settings.DEFAULT_FROM_EMAIL
    from_link = ""  # utils.user_link(from_user)

    shout_name = shout.item.name
    shout_link = ""  # utils.shout_link(shout)

    subject = _('[Shoutit] %(name)s sent you a message regarding: %(about)s') % {
        'name': from_user.first_name, 'about': shout_name}

    reply_to_email = from_user.email

    if to_user.cl_user:
        return

    context = {
        'to': to_name,
        'from': from_name,
        'from_link': from_link,
        'shout_link': shout_link,
        'shout_name': shout_name,
        'message': message_text
    }
    html_template = get_template('message_email.html')
    html_context = Context(context)
    html_message = html_template.render(html_context)

    text_template = get_template('message_email.txt')
    text_context = Context(context)
    text_message = text_template.render(text_context)

    msg = EmailMultiAlternatives(subject, text_message, from_email, [to_email],
                                 headers={'Reply-To': reply_to_email})
    msg.attach_alternative(html_message, "text/html")
    msg.send(True)


def SendUserDealCancel(user, deal):
    subject = _('[ShoutIt] Deal %(name)s has been cancelled') % {'name': deal.item.name}
    to_name = user.name
    deal_link = '%s%s' % (settings.SITE_LINK, constants.DEAL_URL % deal.pk)
    deal_name = deal.item.name

    html_template = get_template('deal_cancel_user.html')
    html_context = Context({
        'to': to_name,
        'deal_link': deal_link,
        'deal_name': deal_name,
        'price': deal.item.price,
        'currency': deal.item.currency.code,
    })
    html_message = html_template.render(html_context)

    text_template = get_template('deal_cancel_user.txt')
    text_context = Context({
        'to': to_name,
        'deal_link': deal_link,
        'deal_name': deal_name,
        'price': deal.item.price,
        'currency': deal.item.currency.code,
    })
    text_message = text_template.render(text_context)

    msg = EmailMultiAlternatives(subject, text_message, settings.DEFAULT_FROM_EMAIL, [user.email])
    msg.attach_alternative(html_message, "text/html")
    msg.send(True)


def SendBusinessDealCancel(deal):
    subject = _('[ShoutIt] Deal %(name)s has been cancelled') % {'name': deal.item.name}
    to_name = deal.Business.name
    deal_link = '%s%s' % (settings.SITE_LINK, constants.DEAL_URL % deal.pk)
    deal_name = deal.item.name

    html_template = get_template('deal_cancel_business.html')
    html_context = Context({
        'to': to_name,
        'deal_link': deal_link,
        'deal_name': deal_name,
    })
    html_message = html_template.render(html_context)

    text_template = get_template('deal_cancel_business.txt')
    text_context = Context({
        'to': to_name,
        'deal_link': deal_link,
        'deal_name': deal_name,
    })
    text_message = text_template.render(text_context)

    msg = EmailMultiAlternatives(subject, text_message, settings.DEFAULT_FROM_EMAIL,
                                 [deal.Business.email])
    msg.attach_alternative(html_message, "text/html")
    msg.send(True)


def SendBusinessSignupEmail(user, email, name):
    subject = _('[ShoutIt] Welcome to ShoutIt!')
    from_email = settings.DEFAULT_FROM_EMAIL
    to = email

    html_template = get_template('business_registration_email.html')
    html_context = Context({
        'email': email,
        'name': name,
    })
    html_message = html_template.render(html_context)

    text_template = get_template('business_registration_email.txt')
    text_context = Context({
        'email': email,
        'name': name,
    })
    text_message = text_template.render(text_context)

    msg = EmailMultiAlternatives(subject, text_message, from_email, [to])
    msg.attach_alternative(html_message, "text/html")

    msg.send(True)


def SendBusinessRejectionEmail(user, email, link):
    subject = _('[ShoutIt] Welcome to ShoutIt!')
    from_email = settings.DEFAULT_FROM_EMAIL
    to = email

    html_template = get_template('business_rejection_email.html')
    html_context = Context({
        'username': user.username,
        'name': user.name,
        'link': link,
    })
    html_message = html_template.render(html_context)

    text_template = get_template('business_rejection_email.txt')
    text_context = Context({
        'username': user.username,
        'name': user.name,
        'link': link,
    })
    text_message = text_template.render(text_context)

    msg = EmailMultiAlternatives(subject, text_message, from_email, [to])
    msg.attach_alternative(html_message, "text/html")

    msg.send(True)


def SendBusinessAcceptanceEmail(user, email, link):
    subject = _('[ShoutIt] Welcome to ShoutIt!')
    from_email = settings.DEFAULT_FROM_EMAIL
    to = email

    html_template = get_template('business_acceptance_email.html')
    html_context = Context({
        'username': user.username,
        'name': user.name,
        'email': email,
        'link': link,
    })
    html_message = html_template.render(html_context)

    text_template = get_template('business_acceptance_email.txt')
    text_context = Context({
        'username': user.username,
        'name': user.name,
        'email': email,
        'link': link,
    })
    text_message = text_template.render(text_context)

    msg = EmailMultiAlternatives(subject, text_message, from_email, [to])
    msg.attach_alternative(html_message, "text/html")

    msg.send(True)


def SendBusinessBuyersDocument(deal, document):
    subject = _('[ShoutIt] Deal %(name)s has been closed') % {'name': deal.item.name}
    to_name = deal.Business.user.get_full_name()
    deal_link = '%s%s' % (settings.SITE_LINK, constants.DEAL_URL % deal.pk)
    deal_name = deal.item.name
    buyers_count = deal.BuyersCount()
    html_template = get_template('deal_close_business.html')
    html_context = Context({
        'to': to_name,
        'deal_link': deal_link,
        'deal_name': deal_name,
        'buyers_count': buyers_count,
    })
    html_message = html_template.render(html_context)

    text_template = get_template('deal_close_business.txt')
    text_context = Context({
        'to': to_name,
        'deal_link': deal_link,
        'deal_name': deal_name,
        'buyers_count': buyers_count,
    })
    text_message = text_template.render(text_context)

    msg = EmailMultiAlternatives(subject, text_message, settings.DEFAULT_FROM_EMAIL,
                                 [deal.Business.user.email])
    msg.attach_alternative(html_message, "text/html")
    msg.attach('%s_vouchers.pdf' % deal_name.replace(' ', '_'), document, 'application/pdf')
    msg.send(True)


def SendUserDealVoucher(buy, voucher):
    subject = _('[ShoutIt] Deal %(name)s has been closed') % {'name': buy.Deal.item.name}
    to_name = buy.user.get_full_name()
    deal_link = '%s%s' % (settings.SITE_LINK, constants.DEAL_URL % buy.Deal.pk)
    deal_name = buy.Deal.item.name
    vouchers_count = buy.Amount
    html_template = get_template('deal_close_user.html')
    html_context = Context({
        'to': to_name,
        'deal_link': deal_link,
        'deal_name': deal_name,
        'vouchers_count': vouchers_count,
    })
    html_message = html_template.render(html_context)

    text_template = get_template('deal_close_user.txt')
    text_context = Context({
        'to': to_name,
        'deal_link': deal_link,
        'deal_name': deal_name,
        'vouchers_count': vouchers_count,
    })
    text_message = text_template.render(text_context)

    msg = EmailMultiAlternatives(subject, text_message, settings.DEFAULT_FROM_EMAIL,
                                 [buy.user.email])
    msg.attach_alternative(html_message, "text/html")
    msg.attach('%s_vouchers.pdf' % deal_name.replace(' ', '_'), voucher, 'application/pdf')
    msg.send(True)


def SendInvitationEmail(from_user, names_emails_dict):
    subject = '%s invites you to join Shoutit' % from_user.get_full_name()
    messages = []
    html_template = get_template('invitation.html')
    text_template = get_template('invitation.txt')
    for name, email in names_emails_dict.iteritems():
        context = Context({
            'from_name': from_user.get_full_name(),
            'from_email': from_user.email,
            'from_link': '%s%s' % (settings.SITE_LINK, constants.PROFILE_URL % from_user.pk),
            'to_name': name,
        })
        html_message = html_template.render(context)
        text_message = text_template.render(context)
        msg = EmailMultiAlternatives(subject, text_message, settings.DEFAULT_FROM_EMAIL,
                                     ['%s <%s>' % (name, email)])
        msg.attach_alternative(html_message, "text/html")
        messages.append(msg)
    connection = get_connection()
    connection.send_messages(messages)
