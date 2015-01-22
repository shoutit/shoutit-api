from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.db.models import Sum
from apps.shoutit.models.base import UUIDModel, AttachedObjectMixin
from apps.shoutit.models.user import Profile
from apps.shoutit.models.business import Business
from django.conf import settings

AUTH_USER_MODEL = getattr(settings, 'AUTH_USER_MODEL')


class PaymentsManager(models.Manager):
    def GetUserPayments(self, user):
        if isinstance(user, AUTH_USER_MODEL):
            return self.filter(user=user)
        elif isinstance(user, basestring):
            return self.filter(user__username__iexact=user)
        elif isinstance(user, Profile):
            return self.filter(user__pk=user.User_id)
        elif isinstance(user, Business):
            return self.filter(user__pk=user.User_id)
        elif isinstance(user, int):
            return self.filter(user__pk=user)

    def GetObjectPayments(self, object):
        return self.filter(content_type=ContentType.objects.get_for_model(object.__class__), object_id=object.pk)


class Payment(UUIDModel, AttachedObjectMixin):
    user = models.ForeignKey(AUTH_USER_MODEL, related_name='Payments')
    DateCreated = models.DateTimeField(auto_now_add=True)
    DateUpdated = models.DateTimeField(auto_now=True)
    Amount = models.FloatField()
    Currency = models.ForeignKey('shoutit.Currency', related_name='+')
    Status = models.IntegerField()
    Transaction = models.ForeignKey('shoutit.Transaction', related_name='Payment')

    objects = PaymentsManager()


class Transaction(UUIDModel):
    RemoteIdentifier = models.CharField(max_length=1024)
    RemoteData = models.CharField(max_length=1024)
    RemoteStatus = models.CharField(max_length=1024)
    DateCreated = models.DateTimeField(auto_now_add=True)
    DateUpdated = models.DateTimeField(auto_now=True)


class Voucher(UUIDModel):
    DealBuy = models.ForeignKey('shoutit.DealBuy', related_name='Vouchers')
    Code = models.CharField(max_length=22)
    DateGenerated = models.DateTimeField(auto_now_add=True)
    IsValidated = models.BooleanField(default=False)
    IsSent = models.BooleanField(default=False)


class DealBuy(UUIDModel):
    Deal = models.ForeignKey('shoutit.Deal', related_name='Buys', on_delete=models.SET_NULL, null=True)
    user = models.ForeignKey(AUTH_USER_MODEL, related_name='DealsBought', on_delete=models.SET_NULL, null=True)
    Amount = models.IntegerField(default=1)
    DateBought = models.DateTimeField(auto_now_add=True)


class Service(UUIDModel):
    Code = models.CharField(max_length=256)
    Name = models.CharField(max_length=1024)
    Price = models.FloatField()


class ServiceManager(models.Manager):
    def GetUserServiceBuyRemaining(self, user, service_code):
        return self.values(ServiceBuy._meta.get_field_by_name('User')[0].column).filter(user=user,
                                                                                        Service__Code__iexact=service_code).annotate(
            buys_count=Sum('Amount')).extra(select={
            'used_count': 'SELECT SUM("%(table)s"."%(amount)s") FROM "%(table)s" WHERE "%(table)s"."%(user_id)s" = %(uid)d AND "%(table)s"."%(service_id)s" IN (%(sid)s)' % {
                'table': ServiceUsage._meta.db_table,
                'user_id': ServiceUsage._meta.get_field_by_name('User')[0].column,
                'uid': user.pk,
                'service_id': ServiceUsage._meta.get_field_by_name('Service')[0].column,
                'sid': """SELECT "%(table)s"."id" FROM "%(table)s" WHERE "%(table)s"."%(code)s" = '%(service_code)s'""" % {
                    'table': Service._meta.db_table,
                    'code': Service._meta.get_field_by_name('Code')[0].column,
                    'service_code': service_code
                },
                'amount': ServiceUsage._meta.get_field_by_name('Amount')[0].column,
            }
        }).values('used_count', 'buys_count')


class ServiceBuy(UUIDModel):
    user = models.ForeignKey(AUTH_USER_MODEL, related_name='Services')
    Service = models.ForeignKey('shoutit.Service', related_name='Buyers')
    Amount = models.IntegerField(default=1)
    DateBought = models.DateTimeField(auto_now_add=True)

    objects = ServiceManager()


class ServiceUsage(UUIDModel):
    user = models.ForeignKey(AUTH_USER_MODEL, related_name='ServicesUsages')
    Service = models.ForeignKey('shoutit.Service', related_name='BuyersUsages')
    Amount = models.IntegerField(default=1)
    DateUsed = models.DateTimeField(auto_now_add=True)


class Subscription(UUIDModel):
    Type = models.IntegerField(default=0)
    State = models.IntegerField(default=0)
    SignUpDate = models.DateTimeField(null=True)
    DeactivateDate = models.DateTimeField(null=True)
    UserName = models.CharField(max_length=64)
    Password = models.CharField(max_length=24)


# PAUSE: PAYPAL
# PAUSE: Payment

#from subscription.signals import subscribed, unsubscribed
#from paypal.standard.ipn.signals import payment_was_successful, payment_was_flagged,subscription_signup,subscription_cancel
#from paypal.standard.pdt.views import pdt
#import re
#
#def paypal_payment_flag(sender, **kwargs):
#	import apps.shoutit.controllers.payment_controller
#	#('Active', 'Cancelled', 'Cleared', 'Completed', 'Denied', 'Paid', 'Pending', 'Processed', 'Refused', 'Reversed', 'Rewarded', 'Unclaimed', 'Uncleared')
#	ipn_obj = sender
#	regex = re.compile(r'(\w+)_(\w+)_User_([^_]+)(?:_x_(\d+))?')
#	match = regex.match(ipn_obj.invoice)
#	transaction_data = 'PayPal TXN %s#%s by %s (%s)' % (ipn_obj.txn_type, ipn_obj.txn_id, ipn_obj.payer_id, ipn_obj.payer_email)
#	transaction_identifier = 'PayPal#%s' % ipn_obj.txn_id
#	if match:
#		item_type, item_id, user_id, amount = match.groups()
#		if ipn_obj.payment_status in ['Completed', 'Paid']:
#			if item_type == 'Deal':
#				apps.shoutit.controllers.payment_controller.PayForDeal(int(user_id), item_id, amount, transaction_data, transaction_identifier)
#			elif item_type == 'Service':
#				apps.shoutit.controllers.payment_controller.PayForService(int(user_id), item_id, amount, transaction_data, transaction_identifier)
#		elif ipn_obj.payment_status in ['Cancelled', 'Reversed', 'Refunded']:
#			transaction_identifier = 'PayPal#%s' % ipn_obj.parent_txn_id
#			if item_type == 'Deal':
#				apps.shoutit.controllers.payment_controller.CancelPaymentForDeal(int(user_id), item_id, transaction_data, transaction_identifier)
#			elif item_type == 'Service':
#				apps.shoutit.controllers.payment_controller.CancelPaymentForService(int(user_id), item_id, transaction_data, transaction_identifier)

#payment_was_successful.connect(paypal_payment_flag)
#payment_was_flagged.connect(paypal_payment_flag)

# taken own payments for now
#def business_subscribed(sender, **kwargs):
#	user = kwargs['user']
#	application = user.BusinessCreateApplication.all()[0]
#	application.Status = BUSINESS_CONFIRMATION_STATUS_WAITING_CONFIRMATION
#	application.save()
#
#def business_unsubscribed(sender, **kwargs):
#	user = kwargs['user']
#	application = user.BusinessCreateApplication.all()[0]
#	application.Status = BUSINESS_CONFIRMATION_STATUS_WAITING_PAYMENT
#	application.save()
#
#subscribed.connect(business_subscribed)
#unsubscribed.connect(business_unsubscribed)


