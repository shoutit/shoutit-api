from django.core.mail.message import EmailMultiAlternatives
from django.template.context import Context
from django.template.loader import get_template
from django.utils.translation import ugettext as _
from django.core.mail import get_connection
from django.conf import settings
from common import constants


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

    msg.send()


def SendPasswordRecoveryEmail(user, email, link):
    subject = _('[ShoutIt] Welcome to ShoutIt!')
    from_email = settings.DEFAULT_FROM_EMAIL
    to = email

    html_template = get_template('password_recovery_email.html')
    html_context = Context({
        'username': user.username,
        'name': user.name,
        'link': link
    })
    html_message = html_template.render(html_context)

    text_template = get_template('password_recovery_email.txt')
    text_context = Context({
        'username': user.username,
        'name': user.name,
        'link': link
    })
    text_message = text_template.render(text_context)

    msg = EmailMultiAlternatives(subject, text_message, from_email, [to])
    msg.attach_alternative(html_message, "text/html")

    msg.send()


def send_signup_email(user):
    subject = _('Welcome to Shoutit!')
    from_email = settings.DEFAULT_FROM_EMAIL
    context = Context({
        'username': user.username,
        'name': user.name if user.name != user.username else '',
        'link': user.verification_link,
        'is_activated': user.is_activated
    })
    html_template = get_template('registration_email.html')
    html_message = html_template.render(context)
    text_template = get_template('registration_email.txt')
    text_message = text_template.render(context)
    msg = EmailMultiAlternatives(subject, text_message, from_email, [user.email])
    msg.attach_alternative(html_message, "text/html")
    msg.send()


def SendListenEmail(follower, followed):
    subject = _('[ShoutIt] %(name)s has started listening to your shouts') % {'name': follower.name}
    link = 'https://%s%s' % (settings.SHOUT_IT_DOMAIN, constants.PROFILE_URL % follower.username)
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
    link = 'https://%s%s' % (settings.SHOUT_IT_DOMAIN, constants.SHOUT_URL % shout.pk)
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

    msg.send()


# todo: links
def SendBuyOfferEmail(shout, buyer):
    subject = u'[Shoutit] %s offered to buy your %s' % (buyer.username, shout.name)
    shout_link = 'https://%s%s' % (settings.SHOUT_IT_DOMAIN, constants.SHOUT_URL % shout.pk)
    buyer_link = 'https://%s%s' % (settings.SHOUT_IT_DOMAIN, constants.PROFILE_URL % buyer.username)
    mute_link = 'https://%s%s' % (settings.SHOUT_IT_DOMAIN, constants.MUTE_URL % shout.pk)
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

    msg = EmailMultiAlternatives(subject, text_message, from_email, [to], headers={'Reply-To': buyer.email})
    msg.attach_alternative(html_message, "text/html")

    msg.send()


def SendSellOfferEmail(shout, seller):
    subject = u'[ShoutIt] %s has %s and willing to sell it to you' % (seller.username, shout.name)
    shout_link = 'https://%s%s' % (settings.SHOUT_IT_DOMAIN, constants.SHOUT_URL % shout.pk)
    seller_link = 'https://%s%s' % (settings.SHOUT_IT_DOMAIN, constants.PROFILE_URL % seller.username)
    mute_link = 'https://%s%s' % (settings.SHOUT_IT_DOMAIN, constants.MUTE_URL % shout.pk)
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

    msg = EmailMultiAlternatives(subject, text_message, from_email, [to], headers={'Reply-To': seller.email})
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
    from_link = "" #utils.user_link(from_user)

    shout_name = shout.item.name
    shout_link = "" #utils.shout_link(shout)

    subject = _('[Shoutit] %(name)s sent you a message regarding: %(about)s') % {'name': from_user.first_name, 'about': shout_name}

    reply_to_email = from_user.email

    if to_user.cl_user:
        from shoutit.models import DBCLConversation
        subject = shout_name
        ref = "%s-%s" % (to_user.cl_ad_id, from_user.pk)
        try:
            DBCLConversation.objects.get(ref=ref)
        except DBCLConversation.DoesNotExist:
            dbcl_conversation = DBCLConversation(ref=ref, from_user=from_user, to_user=to_user, shout=shout)
            dbcl_conversation.save()

        msg = EmailMultiAlternatives(subject, "", "%s <%s>" % (from_name, settings.EMAIL_HOST_USER), [to_email])
        html_message = """
        <p>%s</p>
        <br>
        <br>
        <p style="max-height:1px;min-height:1px;font-size:0;display:none;color:#fffffe">{ref:%s}</p>
        """ % (message_text, ref)
        msg.attach_alternative(html_message, "text/html")
        msg.send()

    else:
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

        msg = EmailMultiAlternatives(subject, text_message, from_email, [to_email], headers={'Reply-To': reply_to_email})
        msg.attach_alternative(html_message, "text/html")
        msg.send()


def SendUserDealCancel(user, deal):
    subject = _('[ShoutIt] Deal %(name)s has been cancelled') % {'name': deal.item.name}
    to_name = user.name
    deal_link = 'https://%s%s' % (settings.SHOUT_IT_DOMAIN, constants.DEAL_URL % deal.pk)
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
    msg.send()


def SendBusinessDealCancel(deal):
    subject = _('[ShoutIt] Deal %(name)s has been cancelled') % {'name': deal.item.name}
    to_name = deal.Business.name
    deal_link = 'https://%s%s' % (settings.SHOUT_IT_DOMAIN, constants.DEAL_URL % deal.pk)
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

    msg = EmailMultiAlternatives(subject, text_message, settings.DEFAULT_FROM_EMAIL, [deal.Business.email])
    msg.attach_alternative(html_message, "text/html")
    msg.send()


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

    msg.send()


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

    msg.send()


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

    msg.send()


def SendBusinessBuyersDocument(deal, document):
    subject = _('[ShoutIt] Deal %(name)s has been closed') % {'name': deal.item.name}
    to_name = deal.Business.user.get_full_name()
    deal_link = 'https://%s%s' % (settings.SHOUT_IT_DOMAIN, constants.DEAL_URL % deal.pk)
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

    msg = EmailMultiAlternatives(subject, text_message, settings.DEFAULT_FROM_EMAIL, [deal.Business.user.email])
    msg.attach_alternative(html_message, "text/html")
    msg.attach('%s_vouchers.pdf' % deal_name.replace(' ', '_'), document, 'application/pdf')
    msg.send()


def SendUserDealVoucher(buy, voucher):
    subject = _('[ShoutIt] Deal %(name)s has been closed') % {'name': buy.Deal.item.name}
    to_name = buy.user.get_full_name()
    deal_link = 'https://%s%s' % (settings.SHOUT_IT_DOMAIN, constants.DEAL_URL % buy.Deal.pk)
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

    msg = EmailMultiAlternatives(subject, text_message, settings.DEFAULT_FROM_EMAIL, [buy.user.email])
    msg.attach_alternative(html_message, "text/html")
    msg.attach('%s_vouchers.pdf' % deal_name.replace(' ', '_'), voucher, 'application/pdf')
    msg.send()


def SendInvitationEmail(from_user, names_emails_dict):
    subject = '%s invites you to join Shoutit' % from_user.get_full_name()
    messages = []
    html_template = get_template('invitation.html')
    text_template = get_template('invitation.txt')
    for name, email in names_emails_dict.iteritems():
        context = Context({
            'from_name': from_user.get_full_name(),
            'from_email': from_user.email,
            'from_link': 'https://%s%s' % (settings.SHOUT_IT_DOMAIN, constants.PROFILE_URL % from_user.pk),
            'to_name': name,
        })
        html_message = html_template.render(context)
        text_message = text_template.render(context)
        msg = EmailMultiAlternatives(subject, text_message, settings.DEFAULT_FROM_EMAIL, ['%s <%s>' % (name, email)])
        msg.attach_alternative(html_message, "text/html")
        messages.append(msg)
    connection = get_connection()
    connection.send_messages(messages)
