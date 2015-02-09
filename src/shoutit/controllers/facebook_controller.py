import json
import urllib
import urllib2
import urlparse

from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings

from shoutit.models import LinkedFacebookAccount
from shoutit.controllers.user_controller import login_without_password, auth_with_facebook, update_profile_location
from settings import SITE_LINK


def user_from_facebook_auth_response(request, auth_response, initial_user=None):

    try:
        response = urllib2.urlopen('https://graph.facebook.com/me?access_token=' + auth_response['accessToken'], timeout=20)
        fb_user = json.loads(response.read())
        if 'email' not in fb_user:
            return KeyError("couldn't access user email"), None
    except urllib2.HTTPError, e:
        return e, None

    try:
        linked_account = LinkedFacebookAccount.objects.get(facebook_id=fb_user['id'])
        user = linked_account.user
    except ObjectDoesNotExist:
        user = None

    if not user:
        long_lived_token = extend_token(auth_response['accessToken'])
        if not long_lived_token:
            return Exception("could not extend the facebook short lived access_token with long lived one"), None

        auth_response['accessToken'] = long_lived_token['access_token']
        auth_response['expiresIn'] = long_lived_token['expires']

        user = auth_with_facebook(request, fb_user, auth_response)

    if user:
        if initial_user and initial_user['location']:
            update_profile_location(user.profile, initial_user['location'])

        login_without_password(request, user)
        return None, user
    else:
        return Exception('Could not login the user'), None


def exchange_code(request, code):
    # Get Access Token using the Code then make an authResponse
    try:
        qs = request.META['QUERY_STRING'].split('&code')[0]
        redirect_uri = urllib.quote('%s%s?%s' % (SITE_LINK, request.path[1:], qs))
        exchange_url = 'https://graph.facebook.com/oauth/access_token?client_id=%s&redirect_uri=%s&client_secret=%s&code=%s' % (
            settings.FACEBOOK_APP_ID,
            redirect_uri,
            settings.FACEBOOK_APP_SECRET,
            code
        )

        response = urllib2.urlopen(exchange_url, timeout=20)
        params = dict(urlparse.parse_qsl(response.read()))
    except Exception, e:
        print e.message
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
        print e.message
        return None

    long_lived_token = {
        'access_token': params['access_token'],
        'expires': params['expires']
    }
    return long_lived_token


def link_facebook_user(request, auth_response):

    long_lived_token = extend_token(auth_response['accessToken'])
    if not long_lived_token:
        return Exception("could not extend the facebook short lived access_token with long lived one"), False

    auth_response['accessToken'] = long_lived_token['access_token']
    auth_response['expiresIn'] = long_lived_token['expires']

    # unlink first
    unlink_facebook_user(request)

    # link
    try:
        la = LinkedFacebookAccount(user=request.user, facebook_id=auth_response['userID'], AccessToken=auth_response['accessToken'], ExpiresIn=auth_response['expiresIn'])
        la.save()
        return None, True
    except Exception, e:
        return e, False


def unlink_facebook_user(request):
    """
    Deleted the user's LinkedFacebookAccount
    :param request:
    :return:
    """
    try:
        linked_account = LinkedFacebookAccount.objects.get(user=request.user)
    except LinkedFacebookAccount.DoesNotExist:
        pass
    else:
        linked_account.delete()
