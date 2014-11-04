from django.core.exceptions import ObjectDoesNotExist
from apps.shoutit.controllers.user_controller import login_without_password, auth_with_facebook, update_location
from apps.shoutit.models import LinkedFacebookAccount
from django.conf import settings
import json
import urllib
import urllib2
import urlparse


def user_from_facebook_auth_response(request, auth_response, initial_user=None):
    long_lived_token = extend_token(auth_response['accessToken'])
    if not long_lived_token:
        return Exception("could not extend the facebook short lived access_token with long lived one"), None

    auth_response['accessToken'] = long_lived_token['access_token']
    auth_response['expiresIn'] = long_lived_token['expires']

    try:
        linked_account = LinkedFacebookAccount.objects.get(AccessToken=auth_response['accessToken'])
        user = linked_account.User
    except ObjectDoesNotExist:
        user = None

    if not user:
        try:
            response = urllib2.urlopen('https://graph.facebook.com/me?access_token=' + auth_response['accessToken'], timeout=20)
            fb_user = json.loads(response.read())
            if not 'email' in fb_user:
                return None
        except urllib2.HTTPError, e:
            return e, None

        user = auth_with_facebook(request, fb_user, auth_response)

    if user:
        if initial_user and initial_user['location']:
            update_location(user.Profile, initial_user['location'])

        login_without_password(request, user)
        request.session['user_renew_location'] = True
        return None, user
    else:
        return Exception('Could not login the user'), None


def exchange_code(request, code):
    # Get Access Token using the Code then make an authResponse
    try:
        qs = request.META['QUERY_STRING'].split('&code')[0]
        redirect_uri = urllib.quote('http%s://%s%s?%s' % ('s' if settings.IS_SITE_SECURE else '',
                                                          settings.SHOUT_IT_DOMAIN, request.path, qs))
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

    auth_response = {
        'accessToken': params['access_token'],
        'expiresIn': params['expires'],
        'signedRequest': 'Code',
    }
    return auth_response


def extend_token(short_lived_token):

    try:
        exchange_url = 'https://graph.facebook.com/oauth/access_token?client_id=%s&client_secret=%s&grant_type=fb_exchange_token&fb_exchange_token=%s' % (settings.FACEBOOK_APP_ID, settings.FACEBOOK_APP_SECRET, short_lived_token)
        response = urllib2.urlopen(exchange_url, timeout=20)
        params = dict(urlparse.parse_qsl(response.read()))
        if not 'access_token' in params:
            return None
    except Exception, e:
        return None

    long_lived_token = {
        'access_token': params['access_token'],
        'expires': params['expires']
    }
    return long_lived_token
