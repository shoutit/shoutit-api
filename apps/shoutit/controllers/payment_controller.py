import hashlib
import re
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from paypal.standard.forms import PayPalEncryptedPaymentsForm
import time
from apps.shoutit import utils

from apps.shoutit.models import Payment, Deal, Transaction, DealBuy, Service, ServiceBuy, Currency
from django.conf import settings

CONCURRENT_DEALS_SERVICE = 'CONCURRENT_DEALS'

def RefundTransaction(transaction):
	pass

def CancelPaymentForService(user, service_code, remote_transaction_data, remote_transaction_identifier):
	pass

def CancelPaymentForDeal(user, deal, remote_transaction_data, remote_transaction_identifier):
	pass

def UpdateOrCreateTransaction(remote_transaction_identifier, remote_transaction_data, status):
	transaction = Transaction.objects.filter(RemoteIdentifier = remote_transaction_identifier)
	old_status = None
	if not transaction:
		transaction = Transaction.objects.create(
			RemoteIdentifier = remote_transaction_identifier,
			RemoteData = remote_transaction_data,
			RemoteStatus = 'Paid'
		)
	else:
		transaction = transaction[0]
		old_status = transaction.RemoteStatus
		transaction.RemoteStatus = status
		transaction.RemoteData = remote_transaction_data
		transaction.save()
	return transaction, old_status

def PayForDeal(user, deal, amount, remote_transaction_data, remote_transaction_identifier):
	import apps.shoutit.controllers.deal_controller as deal_controller

	if not amount:
		amount = 1
	else:
		amount = int(amount)

	deal = Deal.objects.get(pk = deal)
	user = User.objects.get(pk = user)
	transaction, old_status = UpdateOrCreateTransaction(remote_transaction_identifier, remote_transaction_data, 'Paid')
	if old_status != 'Paid':
		deal_buy = deal_controller.BuyDeal(user, deal, amount)
		payment = Payment.objects.create(
			user =  user,
			Amount = deal.Item.Price * amount,
			Currency = deal.Item.Currency,
			Status = 1,
			Transaction = transaction,
			object_pk = deal_buy.pk,
			content_type = ContentType.objects.get_for_model(DealBuy),
		)
		return payment
	else:
		payment = Payment.objects.filter(Transaction = transaction)
		if payment:
			return payment[0]
		else:
			return None

def PayForService(user, service_code, amount, remote_transaction_data, remote_transaction_identifier):
	if not amount:
		amount = 1
	else:
		amount = int(amount)

	service = Service.objects.get(Code = service_code)
	user = User.objects.get(pk = user)
	transaction, old_status = UpdateOrCreateTransaction(remote_transaction_identifier, remote_transaction_data, 'Paid')
	if old_status != 'Paid':
		service_buy = ServiceBuy.objects.create(
			user =  user,
			Service = service,
			Amount = amount
		)
		payment = Payment.objects.create(
			user =  user,
			Amount = service.Price * amount,
			Currency = Currency.objects.get(Code = 'USD'),
			Status = 1,
			Transaction = transaction,
			object_pk = service_buy.pk,
			content_type = ContentType.objects.get_for_model(ServiceBuy),
		)
		return payment
	else:
		payment = Payment.objects.filter(Transaction = transaction)
		if payment:
			return payment[0]
		else:
			return None

def ConvertCurrency(amount, from_currency, to_currency):
	if from_currency == to_currency:
		return amount
	conversion_rate = {
		'AED' : {'USD' : 0.27226400, 'GBP' : 0.17313641, 'EUR' : 0.22116734},
		'USD' : {'AED' : 3.67290571, 'GBP' : 0.63593004, 'EUR' : 0.81234769},
		'GBP' : {'USD' : 1.57250018, 'AED' : 5.77579263, 'EUR' : 1.27741673},
		'EUR' : {'AED' : 4.52146318, 'USD' : 1.23100000, 'GBP' : 0.78282989},
	}
	return amount * conversion_rate[from_currency][to_currency]

def GetPaypalFormForDeal(deal, user, amount = 1):
	return PayPalEncryptedPaymentsForm(initial={
		'notify_url' : settings.PAYPAL_NOTIFY_URL,
		'return' : settings.PAYPAL_RETURN_URL,
		'cancel_return' : settings.PAYPAL_CANCEL_URL,
		'amount' : '%.2f' % ConvertCurrency(deal.Item.Price * amount, deal.Item.Currency.Code, 'USD'),
		'item_name' : '%s by Shoutit' % deal.Item.Name,
		'item_number' : 'Deal_%d' % deal.pk,
		'currency_code' : 'USD',
		'invoice' : 'Deal_%d_User_%d_x_%d' % (deal.pk, user.pk, amount),
		'business' : settings.PAYPAL_BUSINESS, #8FXFX2NN9E83L
	})

def MakePaymentToken(user, payment_type, timestamp = None):
	from datetime import datetime
	from django.utils.http import int_to_base36
	from django.utils.crypto import salted_hmac
	if not timestamp:
		delta = datetime.today() - datetime(2012, 3, 1)
		timestamp = int_to_base36(int(delta.total_seconds()))
	value = (unicode(user.pk) + unicode(user.email) + unicode(payment_type) + unicode(timestamp))
	key_salt = "Sh0u+1t-payment-token-generator"
	hash = salted_hmac(key_salt, value).hexdigest()[::2]
	return "%s-%s" % (timestamp, hash)

def CheckPaymentToken(user, payment_type, token):
	from django.utils.http import base36_to_int
	from datetime import datetime
	try:
		ts_b36, hash = token.split("-")
	except ValueError:
		return False

	try:
		ts = base36_to_int(ts_b36)
	except ValueError:
		return False

	if not token == MakePaymentToken(user, payment_type, ts_b36):
		return False

	delta = datetime.today() - datetime(2012, 3, 1)
	if (delta.total_seconds() - ts) > 900: # 60 * 15
		return False

	return True

def GetPaypalFormForSubscription(user):
	token = MakePaymentToken(user, 'subscription')
	return PayPalEncryptedPaymentsForm(initial={
		'notify_url' : settings.PAYPAL_NOTIFY_URL,
		'return' : settings.PAYPAL_SUBSCRIPTION_RETURN_URL + '%s/' % token,
		'return_url' : settings.PAYPAL_SUBSCRIPTION_RETURN_URL + '%s/' % token,
		'cancel_return' : settings.PAYPAL_SUBSCRIPTION_CANCEL_URL,
		#'amount' : '%.2f' % ConvertCurrency(deal.Item.Price * amount, deal.Item.Currency.Code, 'USD'),
		'item_name' : 'Subscription by Shoutit',
		'item_number' : '1',
		'custom' : '%d' % user.pk,
		'currency_code' : 'USD',
		'amount' : '9.99',
		"a3": "9.99",                      # monthly price
		"p3": 1,                           # duration of each unit (depends on unit)
		"t3": "M",                         # duration unit ("M for Month")
		"src": "1",                        # make payments recur
		"sra": "1",                        # reattempt payment on payment error
		"a1": "0",
		"p1": "6",
		"t1": "M",
		'invoice' : 'Subscription_1_User_%d_%s' % (user.pk, utils.generate_password()[:5]),
		"cmd": "_xclick-subscriptions",
		'business' : settings.PAYPAL_BUSINESS, #8FXFX2NN9E83L
	}, button_type="subscribe")

def GetCPSPFormForDeal(deal, user, amount = 1):
	cpsp_dict = {
		'PSPID' : settings.CPSP_ID,
		'ORDERID' : 'D_%d_U_%d_x_%d_%s' % (deal.pk, user.pk, amount, str(time.time())),  # todo: check
		'AMOUNT' : str(int(deal.Item.Price * amount * 100)),
		'CURRENCY' : deal.Item.Currency.Code,
		'LANGUAGE' : 'en_US',
		'CUID' : str(user.pk),
		'TITLE' : '%s by Shoutit' % deal.Item.Name,
		'ACCEPTURL' : 'http://80.227.53.34/cpsp_accept/',
		'DECLINEURL' : 'http://80.227.53.34/cpsp_decline/',
		'EXCEPTIONURL' : 'http://80.227.53.34/cpsp_exception/',
		'CANCELURL' : 'http://80.227.53.34/cpsp_cancel/',
	}
	h = hashlib.sha512()
	h.update(''.join([k + '=' + cpsp_dict[k] + settings.CPSP_PASS_PHRASE for k in sorted(cpsp_dict.keys())]))
	cpsp_dict['SHASign'] = h.hexdigest()
	return cpsp_dict

def CheckTransaction(pdt):
	regex = re.compile(r'(\w+)_(\w+)_User_([^_]+)(?:_x_(\d+))?')
	match = regex.match(pdt.invoice)
	item_type, item_id, user_id, amount = match.groups()
	if not amount:
		amount = 1
	gross, name, number = None, None, None
	if item_type == 'Deal':
		deal = Deal.objects.filter(pk = item_id)
		if not deal:
			return True, 'Deal not found'
		deal = deal[0]
		gross = '%.2f' % ConvertCurrency(deal.Item.Price * int(amount), deal.Item.Currency.Code, 'USD')
		name = '%s by Shoutit' % deal.Item.Name
		number = 'Deal_%d' % deal.pk
	elif item_type == 'Service':
		pass
	elif item_type == 'Subscription':
		gross = '9.99'
		name = 'Subscription by Shoutit'
		number = '1'
	if gross == str(pdt.mc_gross) and name == pdt.item_name and number == pdt.item_number:
		return False, None
	else:
		print gross, name, number
		print pdt.mc_gross, pdt.item_name, pdt.item_number
		return True, 'Invalid data'


