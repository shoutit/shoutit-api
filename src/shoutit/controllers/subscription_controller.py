from __future__ import unicode_literals
from paypal.standard.ipn.signals import subscription_signup,subscription_cancel,subscription_eot

from common.constants import SUBSCRIPE_BUSINESS, SUBSCRIPTION_TRAIL, SUBSCRIPTION_EXPIRED, SUBSCRIPTION_CANCELED
from shoutit.controllers import business_controller
from shoutit.models import Subscription


def SignUp(sender, **kwargs):
	if sender.custom:
		username = sender.custom
		business = business_controller.GetBusiness(username=username)
		if business.Subscription:
			#TODO check state Canceled-->Forbidden | Trail-->pass
			pass
		else:
			subscription = Subscription(Id = sender.subscr_id,type = SUBSCRIPE_BUSINESS, state = SUBSCRIPTION_TRAIL,SignUpDate = sender.subscr_date)
			subscription.save()
			business.Subscription = subscription
			business.save()

def Expire(sender, **kwargs):
	username = sender.custom
	business = business_controller.GetBusiness(username=username)
	if business:
		if business.Subscription:
			subscription = business.Subscription
			subscription.state = SUBSCRIPTION_EXPIRED
			subscription.DeactivateDate = sender.subscr_date
			subscription.save()

def Cancel(sender, **kwargs):
	username = sender.custom
	business = business_controller.GetBusiness(username=username)
	if business:
		if business.Subscription:
			subscription = business.Subscription
			subscription.DeactivateDate = sender.subscr_date
			subscription.state = SUBSCRIPTION_CANCELED
			subscription.save()


subscription_signup.connect(SignUp)
subscription_eot.connect(Expire)
subscription_cancel.connect(Cancel)