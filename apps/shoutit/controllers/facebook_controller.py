from django.core.exceptions import ObjectDoesNotExist
import json
from apps.shoutit.controllers.user_controller import LoginWithoutPassword, SignUpFB
from apps.shoutit.models import LinkedFacebookAccount
import apps.shoutit.settings
import urllib2, urllib, urlparse

def Auth(request, authResponse):
	long_lived_token = ExtendToken(authResponse['accessToken'])
	authResponse['accessToken'] = long_lived_token['access_token']
	authResponse['expiresIn']  = long_lived_token['expires']

	try:
		linked_account = LinkedFacebookAccount.objects.get(AccessToken = authResponse['accessToken'])
		user = linked_account.User
	except ObjectDoesNotExist,e:
		user = None

	if not user:
		try:
			response = urllib2.urlopen('https://graph.facebook.com/me?access_token=' + authResponse['accessToken'], timeout=20)
			fb_user = json.loads(response.read())
			if not fb_user.has_key('email'):
				return None
		except Exception,e:
			return None
		user = SignUpFB(request, fb_user, authResponse)

	if user:
		LoginWithoutPassword(request, user)
		request.session['user_renew_location'] = True
		return user
	else:
		return None


def ExchangeCode(request, code):
	# Get Access Token using the Code then make an authResponse
	try:
		qs = request.META['QUERY_STRING'].split('&code')[0]
		redirect_uri = urllib.quote('http%s://%s%s?%s'%( 's' if settings.IS_SITE_SECURE else '', settings.SHOUT_IT_DOMAIN, request.path, qs))
		exchange_url = 'https://graph.facebook.com/oauth/access_token?client_id=%s&redirect_uri=%s&client_secret=%s&code=%s' % (
			settings.FACEBOOK_APP_ID,
			redirect_uri,
			settings.FACEBOOK_APP_SECRET,
			code
		)

		response = urllib2.urlopen(exchange_url, timeout=20)
		params = dict(urlparse.parse_qsl(response.read()))
	except Exception,e:
		return None

	authResponse = {
		'accessToken': params['access_token'],
		'expiresIn' : params['expires'],
		'signedRequest' :'Code',
	}
	return authResponse


def ExtendToken(short_lived_token):

	try:
		exchange_url = 'https://graph.facebook.com/oauth/access_token?client_id=%s&client_secret=%s&grant_type=fb_exchange_token&fb_exchange_token=%s' % (settings.FACEBOOK_APP_ID, settings.FACEBOOK_APP_SECRET, short_lived_token)
		response = urllib2.urlopen(exchange_url, timeout=20)
		params = dict(urlparse.parse_qsl(response.read()))
		if not params.has_key('access_token'):
			return None
	except Exception,e:
		return None

	long_lived_token = {
		'access_token' : params['access_token'],
		'expires' : params['expires']
	}
	return long_lived_token
