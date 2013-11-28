import re
from django.contrib.auth.models import User
from django.http import HttpResponseRedirect
from django.template import RequestContext
from django.shortcuts import render_to_response
from paypal.standard.pdt.models import PayPalPDT
from paypal.standard.pdt.forms import PayPalPDTForm
from apps.shoutit.constants import BUSINESS_CONFIRMATION_STATUS_WAITING_PAYMENT_CONFIRMATION
import apps.shoutit.controllers.payment_controller

def pdt(request,):
	"""Payment data transfer implementation: http://tinyurl.com/c9jjmw"""
	context = {}
	pdt_obj = None
	txn_id = request.GET.get('tx')
	failed = False
	if txn_id is not None:
		try:
			pdt_obj = PayPalPDT.objects.get(txn_id=txn_id)
		except PayPalPDT.DoesNotExist:
			pass

		if pdt_obj is None:
			form = PayPalPDTForm(request.GET)
			error = None
			if form.is_valid():
				try:
					pdt_obj = form.save(commit=False)
				except Exception, e:
					error = repr(e)
					failed = True
			else:
				error = form.errors
				failed = True

			if failed:
				pdt_obj = PayPalPDT()
				pdt_obj.set_flag("Invalid form. %s" % error)

			pdt_obj.initialize(request)

			if not failed:
				pdt_obj.verify(apps.shoutit.controllers.payment_controller.CheckTransaction)
	else:
		pass

	context.update({"failed":failed, "pdt_obj":pdt_obj})
#	if failed:
#		return render_to_response('pdt.html', context, RequestContext(request))
#	else:
#		regex = re.compile(r'(\w+)_(\w+)_User_([^_]+)(?:_x_(\d+))?')
#		match = regex.match(pdt_obj.invoice)
#		item_type, item_id, user_id, amount = match.groups()
#		if not amount:
#			amount = 1
#		if item_type == 'Deal':
#			pass
#		elif item_type == 'Service':
#			pass
#		elif item_type == 'Subscription':
#			user = User.objects.get(pk = int(user_id))
#			application = user.BusinessCreateApplication.all()[0]
#			application.Status = BUSINESS_CONFIRMATION_STATUS_WAITING_PAYMENT_CONFIRMATION
#			application.save()
	return HttpResponseRedirect('/bsignup/')
