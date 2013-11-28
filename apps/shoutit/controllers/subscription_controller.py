import datetime
from paypal.standard.ipn.signals import subscription_signup,subscription_cancel,subscription_eot
import re
from apps.shoutit.constants import SUBSCRIPE_BUSINESS, SUBSCRIPTION_TRAIL, SUBSCRIPTION_EXPIRED, SUBSCRIPTION_CANCELED
from apps.shoutit.controllers import business_controller
from apps.shoutit.models import Subscription

def SignUp(sender, **kwargs):
	if sender.custom:
		username = sender.custom
		business = business_controller.GetBusiness(username=username)
		if business.Subscription:
			#TODO check state Canceled-->Forbidden | Trail-->pass
			pass
		else:
			subscription = Subscription(Id = sender.subscr_id,Type = SUBSCRIPE_BUSINESS,State = SUBSCRIPTION_TRAIL,SignUpDate = sender.subscr_date)
			subscription.save()
			business.Subscription = subscription
			business.save()

def Expire(sender, **kwargs):
	username = sender.custom
	business = business_controller.GetBusiness(username=username)
	if business:
		if business.Subscription:
			subscription = business.Subscription
			subscription.State = SUBSCRIPTION_EXPIRED
			subscription.DeactivateDate = sender.subscr_date
			subscription.save()

def Cancel(sender, **kwargs):
	username = sender.custom
	business = business_controller.GetBusiness(username=username)
	if business:
		if business.Subscription:
			subscription = business.Subscription
			subscription.DeactivateDate = sender.subscr_date
			subscription.State = SUBSCRIPTION_CANCELED
			subscription.save()


subscription_signup.connect(SignUp)
subscription_eot.connect(Expire)
subscription_cancel.connect(Cancel)