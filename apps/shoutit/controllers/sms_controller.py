from datetime import datetime
import urllib
import urllib2
from suds.client import Client
from xml.dom.minidom import parseString
from ShoutWebsite.utils import asynchronous_task
import settings

def LogIn():
	client = Client(settings.SMS_SERVICE_WSDL_URL)
	t = client.service.apiValidateLogin(settings.SMS_SERVICE_USERNAME, settings.SMS_SERVICE_PASSWORD)
	dom = parseString(t)
	err_code = int(dom.getElementsByTagName("resp")[0].getAttribute("err"))
	if err_code:
		return None
	ticket = dom.getElementsByTagName("ticket")[0].toxml().replace('<ticket>','').replace('</ticket>','')
	return ticket


def LogOut(ticket, client = None):
	if client is None:
		client = Client(settings.SMS_SERVICE_WSDL_URL)
	t = client.service.apiLogout(ticket)
	dom = parseString(t)
	err_code = int(dom.getElementsByTagName("resp")[0].getAttribute("err"))
	if err_code:
		return
	return

@asynchronous_task()
def SendSMS2(from_num='Shoutit.com', to_num='', text='', schedule = None):
	try:
		text = urllib.quote(text)
		sms_url = 'https://www.smsglobal.com/http-api.php?&action=sendsms&user=syrexme&password=25600696&from=%s&to=%s&text=%s' %(from_num, to_num, text)
		sms_res = urllib2.urlopen(sms_url,timeout=10).read() or ''
		if sms_res.find('OK: 0') != -1:
			return True
		else:
			return False
	except BaseException,e:
		return False

@asynchronous_task()
def SendSMS(ticket, to_num, from_num, text, schedule = None, client = None):
	if client is None:
		client = Client(settings.SMS_SERVICE_WSDL_URL)
	b = client.service.apiBalanceSms(ticket)
	dom = parseString(b)
	err_code = int(dom.getElementsByTagName("resp")[0].getAttribute("err"))
	if err_code:
		return
	balance = float(dom.getElementsByTagName("balance")[0].toxml().replace('<balance>','').replace('</balance>',''))
	if balance <= 0:
		return
	s_date = ''
	if schedule is not None:
		if schedule > datetime.now():
			return
		s_date = schedule.strftime('%Y-%m-%d %H:%M:%S')
	client.service.apiSendSms(ticket, from_num, to_num, text, 'text', '0', s_date)
	return