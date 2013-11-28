from django.conf import settings
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from django.db.models.query_utils import Q
from django.http import HttpResponseRedirect, HttpResponseBadRequest, HttpResponse
from django.utils.http import urlquote
from urllib import urlencode

from django.views.decorators.csrf import csrf_exempt
from piston.authentication.oauth.store import store, InvalidConsumerError, InvalidTokenError
from piston.authentication.oauth.utils import verify_oauth_request, get_oauth_request, require_params
from apps.shoutit.models import LinkedFacebookAccount

@csrf_exempt
def get_request_token(request):
	oauth_request = get_oauth_request(request)
	missing_params = require_params(oauth_request) #, ('oauth_callback',)
	if missing_params is not None:
		return missing_params
	try:
		consumer = store.get_consumer(request, oauth_request, oauth_request['oauth_consumer_key'])
	except InvalidConsumerError:
		return HttpResponseBadRequest('Invalid Consumer.')

	if not verify_oauth_request(request, oauth_request, consumer):
		return HttpResponseBadRequest('Could not verify OAuth request.')

	request_token = store.create_request_token(request, oauth_request, consumer , 'oob') #"oob"

	ret = urlencode({
		'oauth_token': request_token.key,
		'oauth_token_secret': request_token.secret,
		'oauth_callback_confirmed': 'true'
	})
	
	return HttpResponse(ret, content_type='application/x-www-form-urlencoded')

@csrf_exempt
def get_access_token(request):
	oauth_request = get_oauth_request(request)

	if 'oauth_token' not in oauth_request:
		return HttpResponseBadRequest('No request token specified.')

	try:
		request_token = store.get_request_token(request, oauth_request, oauth_request['oauth_token'])
	except InvalidTokenError:
		return HttpResponseBadRequest('Invalid request token.')

	consumer = store.get_consumer_for_request_token(request, oauth_request, request_token)

	if not request.REQUEST.has_key('credential') or not request.REQUEST.has_key('password'):
		return HttpResponseBadRequest('Invalid username or password.')
	credential = request.REQUEST['credential']
	password = request.REQUEST['password']

	if not credential or not password:
		return HttpResponseBadRequest('Invalid username or password.')

	try:
		user = User.objects.get(Q(username__iexact = credential.strip()) | Q(email__iexact = credential.strip()) | Q(Profile__Mobile__iexact = credential.strip()))
	except ObjectDoesNotExist:
		return HttpResponseBadRequest('Invalid username or password.')
	except MultipleObjectsReturned:
		return HttpResponseBadRequest('Invalid username or password.')

	if not user.check_password(password.strip()):
		return HttpResponseBadRequest('Invalid username or password.')

	request.user = user
	request_token = store.authorize_request_token(request, oauth_request, request_token)
	access_token = store.create_access_token(request, oauth_request, consumer, request_token)

	response = '%s\0%s' % (access_token.key, access_token.secret)
	return HttpResponse(response)

@csrf_exempt
def get_facebook_token(request):
	oauth_request = get_oauth_request(request)

	if 'oauth_token' not in oauth_request:
		return HttpResponseBadRequest('No request token specified.')

	try:
		request_token = store.get_request_token(request, oauth_request, oauth_request['oauth_token'])
	except InvalidTokenError:
		return HttpResponseBadRequest('Invalid request token.')

	consumer = store.get_consumer_for_request_token(request, oauth_request, request_token)

	if not request.REQUEST.has_key('access_token'):
		return HttpResponseBadRequest('Invalid access token.')

	try:
		linked_account = LinkedFacebookAccount.objects.get(AccessToken = request.REQUEST['access_token'])
		user = linked_account.User
	except ObjectDoesNotExist:
		return HttpResponseBadRequest('Invalid access token.')

	request.user = user
	request_token = store.authorize_request_token(request, oauth_request, request_token)
	access_token = store.create_access_token(request, oauth_request, consumer, request_token)

	response = '%s\0%s' % (access_token.key, access_token.secret)
	return HttpResponse(response)

class DjangoAuthentication(object):
	"""
	Django authentication.
	"""
	def __init__(self, login_url=None, redirect_field_name=REDIRECT_FIELD_NAME):
		if not login_url:
			login_url = settings.LOGIN_URL
		self.login_url = login_url
		self.redirect_field_name = redirect_field_name
		self.request = None

	def is_authenticated(self, request):
		"""
		This method call the `is_authenticated` method of django
		User in django.contrib.auth.models.

		`is_authenticated`: Will be called when checking for
		authentication. It returns True if the user is authenticated
		False otherwise.
		"""
		self.request = request
		return request.user.is_authenticated()

	def challenge(self):
		"""
		`challenge`: In cases where `is_authenticated` returns
		False, the result of this method will be returned.
		This will usually be a `HttpResponse` object with
		some kind of challenge headers and 401 code on it.
		"""
		path = urlquote(self.request.get_full_path())
		tup = self.login_url, self.redirect_field_name, path
		return HttpResponseRedirect('%s?%s=%s' % tup)