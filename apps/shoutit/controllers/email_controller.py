from django.core.mail.message import EmailMultiAlternatives
from django.template.context import Context
from django.template.loader import get_template
from django.utils.translation import ugettext as _
from django.core.mail import get_connection
from apps.shoutit.utils import asynchronous_task
import apps.shoutit.settings

@asynchronous_task()
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

@asynchronous_task()
def SendPasswordRecoveryEmail(user, email, link):
	subject = _('[ShoutIt] Welcome to ShoutIt!')
	from_email = settings.DEFAULT_FROM_EMAIL
	to = email

	html_template = get_template('password_recovery_email.html')
	html_context = Context({
		'username'	: user.username,
		'name'		: user.name(),
		'link'		: link
	})
	html_message = html_template.render(html_context)

	text_template = get_template('password_recovery_email.txt')
	text_context = Context({
		'username' : user.username,
		'name'		: user.name(),
		'link' : link
	})
	text_message = text_template.render(text_context)

	msg = EmailMultiAlternatives(subject, text_message, from_email, [to])
	msg.attach_alternative(html_message, "text/html")

	msg.send()

@asynchronous_task()
def SendRegistrationActivationEmail(user, email, link, token):
	subject = _('[ShoutIt] Welcome to ShoutIt!')
	from_email = settings.DEFAULT_FROM_EMAIL
	to = email

	html_template = get_template('registration_email.html')
	html_context = Context({
		'username'	: user.username,
		'name'		: user.name(),
		'link' 		: link,
		'token'		: token
		})
	html_message = html_template.render(html_context)

	text_template = get_template('registration_email.txt')
	text_context = Context({
		'username'  : user.username,
		'name'		: user.name(),
		'link' 		: link,
		'token'		: token
		})
	text_message = text_template.render(text_context)

	msg = EmailMultiAlternatives(subject, text_message, from_email, [to])
	msg.attach_alternative(html_message, "text/html")

	msg.send()

@asynchronous_task()
def SendFollowshipEmail(follower, followed):
	subject = _('[ShoutIt] %(name)s has started listening to your shouts') % { 'name' : follower.name() }
	link = 'http%s://%s%s' % (settings.IS_SITE_SECURE and 's' or '', settings.SHOUT_IT_DOMAIN, constants.PROFILE_URL % follower.username)
	from_email = settings.DEFAULT_FROM_EMAIL
	to = followed.email

	html_template = get_template('followship_email.html')
	html_context = Context({
		'followed' : followed.name(),
		'follower' : follower.name(),
		'link' : link
	})
	html_message = html_template.render(html_context)

	text_template = get_template('followship_email.txt')
	text_context = Context({
		'followed' : followed.name(),
		'follower' : follower.name(),
		'link' : link
	})
	text_message = text_template.render(text_context)

	msg = EmailMultiAlternatives(subject, text_message, from_email, [to])
	msg.attach_alternative(html_message, "text/html")
	msg.send(True)

@asynchronous_task()
def SendExpiryNotificationEmail(user, shout):
	subject = _('[ShoutIt] your shout is about to expire! reshout it now.')
	title = shout.Item.Name
	link = 'http%s://%s%s' % (settings.IS_SITE_SECURE and 's' or '', settings.SHOUT_IT_DOMAIN, constants.SHOUT_URL % utils.IntToBase62(shout.id))
	from_email = settings.DEFAULT_FROM_EMAIL
	to = user.email

	html_template = get_template('expiry_email.html')
	html_context = Context({
		'username' : user.first_name + ' ' + user.lastname,
		'title' : title,
		'link' : link
	})
	html_message = html_template.render(html_context)

	text_template = get_template('expiry_email.txt')
	text_context = Context({
		'username' : user.first_name + ' ' + user.lastname,
		'title' : title,
		'link' : link
	})
	text_message = text_template.render(text_context)

	msg = EmailMultiAlternatives(subject, text_message, from_email, [to])
	msg.attach_alternative(html_message, "text/html")

	msg.send()

@asynchronous_task()
def SendBuyOfferEmail(shout, buyer):
	subject = u'[ShoutIt] %s offered to buy your %s' % (buyer.username, shout.Name)
	shout_link = 'http%s://%s%s' % (settings.IS_SITE_SECURE and 's' or '', settings.SHOUT_IT_DOMAIN, constants.SHOUT_URL % (utils.EntityID(shout)))
	buyer_link = 'http%s://%s%s' % (settings.IS_SITE_SECURE and 's' or '', settings.SHOUT_IT_DOMAIN, constants.PROFILE_URL % buyer.username)
	mute_link = 'http%s://%s%s' % (settings.IS_SITE_SECURE and 's' or '', settings.SHOUT_IT_DOMAIN, constants.MUTE_URL % (utils.EntityID(shout)))
	from_email = settings.DEFAULT_FROM_EMAIL
	to = shout.OwnerUser.email

	html_template = get_template('buy_offer_email.html')
	html_context = Context({
		'username' : shout.OwnerUser.username,
		'buyer' : buyer.username,
		'shout_link' : shout_link,
		'buyer_link' : buyer_link,
		'mute_link' : mute_link,
		'buyer_email' : buyer.email
	})
	html_message = html_template.render(html_context)

	text_template = get_template('buy_offer_email.txt')
	text_context =  Context({
		'username' : shout.OwnerUser.username,
		'buyer' : buyer.username,
		'shout_link' : shout_link,
		'buyer_link' : buyer_link,
		'mute_link' : mute_link,
		'buyer_email' : buyer.email
	})
	text_message = text_template.render(text_context)

	msg = EmailMultiAlternatives(subject, text_message, from_email, [to], headers = {'Reply-To' : buyer.email})
	msg.attach_alternative(html_message, "text/html")

	msg.send()

@asynchronous_task()
def SendSellOfferEmail(shout, seller):
	subject = u'[ShoutIt] %s has %s and willing to sell it to you' % (seller.username, shout.Name)
	shout_link = 'http%s://%s%s' % (settings.IS_SITE_SECURE and 's' or '', settings.SHOUT_IT_DOMAIN, constants.SHOUT_URL % (utils.EntityID(shout)))
	seller_link = 'http%s://%s%s' % (settings.IS_SITE_SECURE and 's' or '', settings.SHOUT_IT_DOMAIN, constants.PROFILE_URL % seller.username)
	mute_link = 'http%s://%s%s' % (settings.IS_SITE_SECURE and 's' or '', settings.SHOUT_IT_DOMAIN, constants.MUTE_URL % (utils.EntityID(shout)))
	from_email = settings.DEFAULT_FROM_EMAIL
	to = shout.OwnerUser.email

	html_template = get_template('sell_offer_email.html')
	html_context = Context({
		'username' : shout.OwnerUser.username,
		'buyer' : seller.username,
		'shout_link' : shout_link,
		'seller_link' : seller_link,
		'mute_link' : mute_link,
		'seller_email' : seller.email
	})
	html_message = html_template.render(html_context)

	text_template = get_template('sell_offer_email.txt')
	text_context = Context({
		'username' : shout.OwnerUser.username,
		'buyer' : seller.username,
		'shout_link' : shout_link,
		'seller_link' : seller_link,
		'mute_link' : mute_link,
		'seller_email' : seller.email
	})
	text_message = text_template.render(text_context)

	msg = EmailMultiAlternatives(subject, text_message, from_email, [to], headers = {'Reply-To' : seller.email})
	msg.attach_alternative(html_message, "text/html")

	msg.send()

@asynchronous_task()
def SendMessageEmail(message):
	user = message.ToUser

	if not user.is_active and apps.shoutit.controllers.user_controller.GetProfile(user).Mobile:
		shout = message.Conversation.AboutPost
		content = utils.RemoveNonAscii(shout.Item.Name)
		title = utils.get_shout_name_preview(content,25)
		link = 'shoutit.com/' + apps.shoutit.controllers.user_controller.GetProfile(user).LastToken.Token
		msg = utils.get_shout_name_preview(utils.RemoveNonAscii(message.Text),30)

		text = _('A Shouter has replied to your ad \'%(shout_title)s\' on Shoutit, visit %(link)s to make your deal happen.\n-\n"%(message)s"') % {'shout_title' : title, 'link' : link, 'message' : msg}
		mobile = apps.shoutit.controllers.user_controller.GetProfile(user).Mobile
		apps.shoutit.controllers.sms_controller.SendSMS2('ShoutIt.com',mobile, text)
		return

	subject = _('[ShoutIt] %(name)s has sent you a message') % {'name' : message.FromUser.get_full_name()}
	to_name = message.ToUser.name()
	from_name = message.FromUser.name()
	from_link = 'http%s://%s%s' % (settings.IS_SITE_SECURE and 's' or '', settings.SHOUT_IT_DOMAIN, constants.PROFILE_URL % message.FromUser.username)
	shout_link = 'http%s://%s%s' % (settings.IS_SITE_SECURE and 's' or '', settings.SHOUT_IT_DOMAIN, constants.SHOUT_URL % (utils.EntityID(message.Conversation.AboutPost)))
	shout_name = message.Conversation.AboutPost.Item.Name
	message_text = message.Text

	html_template = get_template('message_email.html')
	html_context = Context({
		'to' : to_name,
		'from' : from_name,
		'from_link' : from_link,
		'shout_link' : shout_link,
		'shout_name' : shout_name,
		'message' : message_text
	})
	html_message = html_template.render(html_context)

	text_template = get_template('message_email.txt')
	text_context = Context({
		'to' : to_name,
		'from' : from_name,
		'from_link' : from_link,
		'shout_link' : shout_link,
		'shout_name' : shout_name,
		'message' : message_text
	})
	text_message = text_template.render(text_context)

	msg = EmailMultiAlternatives(subject, text_message, settings.DEFAULT_FROM_EMAIL, [message.ToUser.email], headers = {'Reply-To' : message.FromUser.email})
	msg.attach_alternative(html_message, "text/html")
	msg.send()

@asynchronous_task()
def SendUserDealCancel(user, deal):
	subject = _('[ShoutIt] Deal %(name)s has been cancelled') % {'name' : deal.Item.Name}
	to_name = user.name()
	deal_link = 'http%s://%s%s' % (settings.IS_SITE_SECURE and 's' or '', settings.SHOUT_IT_DOMAIN, constants.DEAL_URL % (utils.EntityID(deal)))
	deal_name = deal.Item.Name

	html_template = get_template('deal_cancel_user.html')
	html_context = Context({
		'to' : to_name,
		'deal_link' : deal_link,
		'deal_name' : deal_name,
		'price' : deal.Item.Price,
		'currency' : deal.Item.Currency.Code,
	})
	html_message = html_template.render(html_context)

	text_template = get_template('deal_cancel_user.txt')
	text_context = Context({
		'to' : to_name,
		'deal_link' : deal_link,
		'deal_name' : deal_name,
		'price' : deal.Item.Price,
		'currency' : deal.Item.Currency.Code,
	})
	text_message = text_template.render(text_context)

	msg = EmailMultiAlternatives(subject, text_message, settings.DEFAULT_FROM_EMAIL, [user.email])
	msg.attach_alternative(html_message, "text/html")
	msg.send()

@asynchronous_task()
def SendBusinessDealCancel(deal):
	subject = _('[ShoutIt] Deal %(name)s has been cancelled') % {'name' : deal.Item.Name}
	to_name = deal.BusinessProfile.name()
	deal_link = 'http%s://%s%s' % (settings.IS_SITE_SECURE and 's' or '', settings.SHOUT_IT_DOMAIN, constants.DEAL_URL % (utils.EntityID(deal)))
	deal_name = deal.Item.Name

	html_template = get_template('deal_cancel_business.html')
	html_context = Context({
		'to' : to_name,
		'deal_link' : deal_link,
		'deal_name' : deal_name,
	})
	html_message = html_template.render(html_context)

	text_template = get_template('deal_cancel_business.txt')
	text_context = Context({
		'to' : to_name,
		'deal_link' : deal_link,
		'deal_name' : deal_name,
	})
	text_message = text_template.render(text_context)

	msg = EmailMultiAlternatives(subject, text_message, settings.DEFAULT_FROM_EMAIL, [deal.BusinessProfile.email])
	msg.attach_alternative(html_message, "text/html")
	msg.send()

@asynchronous_task()
def SendBusinessSignupEmail(user, email, name):
	subject = _('[ShoutIt] Welcome to ShoutIt!')
	from_email = settings.DEFAULT_FROM_EMAIL
	to = email

	html_template = get_template('business_registration_email.html')
	html_context = Context({
		'email'		: email,
		'name'		: name,
		})
	html_message = html_template.render(html_context)

	text_template = get_template('business_registration_email.txt')
	text_context = Context({
		'email'		: email,
		'name'		: name,
		})
	text_message = text_template.render(text_context)

	msg = EmailMultiAlternatives(subject, text_message, from_email, [to])
	msg.attach_alternative(html_message, "text/html")

	msg.send()

@asynchronous_task()
def SendBusinessRejectionEmail(user, email, link):
	subject = _('[ShoutIt] Welcome to ShoutIt!')
	from_email = settings.DEFAULT_FROM_EMAIL
	to = email

	html_template = get_template('business_rejection_email.html')
	html_context = Context({
		'username'	: user.username,
		'name'		: user.name(),
		'link'		: link,
		})
	html_message = html_template.render(html_context)

	text_template = get_template('business_rejection_email.txt')
	text_context = Context({
		'username'  : user.username,
		'name'		: user.name(),
		'link'      : link,
		})
	text_message = text_template.render(text_context)

	msg = EmailMultiAlternatives(subject, text_message, from_email, [to])
	msg.attach_alternative(html_message, "text/html")

	msg.send()

@asynchronous_task()
def SendBusinessAcceptanceEmail(user, email, link):
	subject = _('[ShoutIt] Welcome to ShoutIt!')
	from_email = settings.DEFAULT_FROM_EMAIL
	to = email

	html_template = get_template('business_acceptance_email.html')
	html_context = Context({
		'username'	: user.username,
		'name'		: user.name(),
		'email'		: email,
		'link'		: link,
		})
	html_message = html_template.render(html_context)

	text_template = get_template('business_acceptance_email.txt')
	text_context = Context({
		'username'  : user.username,
		'name'		: user.name(),
		'email'		: email,
		'link'      : link,
		})
	text_message = text_template.render(text_context)

	msg = EmailMultiAlternatives(subject, text_message, from_email, [to])
	msg.attach_alternative(html_message, "text/html")

	msg.send()

@asynchronous_task()
def SendBusinessBuyersDocument(deal, document):
	subject = _('[ShoutIt] Deal %(name)s has been closed') % {'name' : deal.Item.Name}
	to_name = deal.BusinessProfile.User.get_full_name()
	deal_link = 'http%s://%s%s' % (settings.IS_SITE_SECURE and 's' or '', settings.SHOUT_IT_DOMAIN, constants.DEAL_URL % (utils.EntityID(deal)))
	deal_name = deal.Item.Name
	buyers_count = deal.BuyersCount()
	html_template = get_template('deal_close_business.html')
	html_context = Context({
		'to' : to_name,
		'deal_link' : deal_link,
		'deal_name' : deal_name,
		'buyers_count' : buyers_count,
	})
	html_message = html_template.render(html_context)

	text_template = get_template('deal_close_business.txt')
	text_context = Context({
		'to' : to_name,
		'deal_link' : deal_link,
		'deal_name' : deal_name,
		'buyers_count' : buyers_count,
	})
	text_message = text_template.render(text_context)

	msg = EmailMultiAlternatives(subject, text_message, settings.DEFAULT_FROM_EMAIL, [deal.BusinessProfile.User.email])
	msg.attach_alternative(html_message, "text/html")
	msg.attach('%s_vouchers.pdf' % deal_name.replace(' ', '_'), document, 'application/pdf')
	msg.send()

@asynchronous_task()
def SendUserDealVoucher(buy, voucher):
	subject = _('[ShoutIt] Deal %(name)s has been closed') % {'name' : buy.Deal.Item.Name}
	to_name = buy.User.get_full_name()
	deal_link = 'http%s://%s%s' % (settings.IS_SITE_SECURE and 's' or '', settings.SHOUT_IT_DOMAIN, constants.DEAL_URL % (utils.EntityID(buy.Deal)))
	deal_name = buy.Deal.Item.Name
	vouchers_count = buy.Amount
	html_template = get_template('deal_close_user.html')
	html_context = Context({
		'to' : to_name,
		'deal_link' : deal_link,
		'deal_name' : deal_name,
		'vouchers_count' : vouchers_count,
	})
	html_message = html_template.render(html_context)

	text_template = get_template('deal_close_user.txt')
	text_context = Context({
		'to' : to_name,
		'deal_link' : deal_link,
		'deal_name' : deal_name,
		'vouchers_count' : vouchers_count,
	})
	text_message = text_template.render(text_context)

	msg = EmailMultiAlternatives(subject, text_message, settings.DEFAULT_FROM_EMAIL, [buy.User.email])
	msg.attach_alternative(html_message, "text/html")
	msg.attach('%s_vouchers.pdf' % deal_name.replace(' ', '_'), voucher, 'application/pdf')
	msg.send()

@asynchronous_task()
def SendInvitationEmail(from_user, names_emails_dict):
	subject = '%s invites you to join Shoutit' % from_user.get_full_name()
	messages = []
	html_template = get_template('invitation.html')
	text_template = get_template('invitation.txt')
	for name, email in names_emails_dict.iteritems():
		context = Context({
			'from_name' : from_user.get_full_name(),
			'from_email' : from_user.email,
			'from_link' : 'http%s://%s%s' % (settings.IS_SITE_SECURE and 's' or '', settings.SHOUT_IT_DOMAIN, constants.PROFILE_URL % (utils.EntityID(from_user))),
			'to_name' : name,
		})
		html_message = html_template.render(context)
		text_message = text_template.render(context)
		msg = EmailMultiAlternatives(subject, text_message, settings.DEFAULT_FROM_EMAIL, ['%s <%s>' % (name, email)])
		msg.attach_alternative(html_message, "text/html")
		messages.append(msg)
	connection = get_connection(backend = 'django.core.mail.backends.smtp.EmailBackend', fail_silently = True, host = settings.SEND_GRID_SMTP_HOST, username = settings.SEND_GRID_SMTP_USERNAME, password = settings.SEND_GRID_SMTP_PASSWORD)
	connection.send_messages(messages)
	
from apps.shoutit import constants, utils
import apps.shoutit.controllers.sms_controller
import apps.shoutit.controllers.user_controller