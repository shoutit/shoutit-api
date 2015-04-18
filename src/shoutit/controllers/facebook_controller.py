# -*- coding: utf-8 -*-
"""

"""
from __future__ import unicode_literals
import json
import urllib
import urllib2
import urlparse

from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings
from rest_framework.exceptions import ValidationError

from shoutit.models import LinkedFacebookAccount
from shoutit.controllers.user_controller import auth_with_facebook, update_profile_location


def user_from_facebook_auth_response(auth_response, initial_user=None):
    try:
        access_token = auth_response['accessToken']
    except (KeyError, TypeError):
        access_token = auth_response

    try:
        response = urllib2.urlopen('https://graph.facebook.com/me?access_token={}'.format(access_token), timeout=20)
        fb_user = json.loads(response.read())
        if 'email' not in fb_user:
            return KeyError("couldn't access user email"), None
    except urllib2.HTTPError, e:
        return Exception("Invalid facebook accessToken"), None

    try:
        linked_account = LinkedFacebookAccount.objects.get(facebook_id=fb_user['id'])
        user = linked_account.user
    except ObjectDoesNotExist:
        user = None

    if not user:
        long_lived_token = extend_token(access_token)
        if not long_lived_token:
            return Exception("could not extend the facebook short lived access_token with long lived one"), None

        user = auth_with_facebook(fb_user, long_lived_token)

    if user:
        if initial_user and initial_user['location']:
            update_profile_location(user.profile, initial_user['location'])

        return None, user
    else:
        return Exception('Could not login the user'), None


def exchange_code(request, code):
    # Get Access Token using the Code then make an authResponse
    try:
        qs = request.META['QUERY_STRING'].split('&code')[0]
        redirect_uri = urllib.quote('%s%s?%s' % (settings.SITE_LINK, request.path[1:], qs))
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
    }
    return auth_response


def extend_token(short_lived_token):

    try:
        query = "client_id={}&client_secret={}&grant_type=fb_exchange_token&fb_exchange_token={}".format(
            settings.FACEBOOK_APP_ID, settings.FACEBOOK_APP_SECRET, short_lived_token
        )
        exchange_url = 'https://graph.facebook.com/oauth/access_token?{}'.format(query)

        response = urllib2.urlopen(exchange_url, timeout=20)
        params = dict(urlparse.parse_qsl(response.read()))
        if 'access_token' not in params:
            return None
    except Exception, e:
        print e.message
        # todo: log_error
        return None

    long_lived_token = {
        'access_token': params['access_token'],
        'expires': params['expires']
    }
    return long_lived_token


def link_facebook_account(user, facebook_access_token):

    long_lived_token = extend_token(facebook_access_token)
    if not long_lived_token:
        raise ValidationError({'facebook_access_token': "could not extend the facebook short lived access_token with long lived one"})

    # todo: get info, pic, etc about user
    try:
        response = urllib2.urlopen('https://graph.facebook.com/me?access_token={}'.format(long_lived_token['access_token']), timeout=20)
        fb_user = json.loads(response.read())
    except urllib2.HTTPError, e:
        raise ValidationError({'error': "could not link facebook account"})

    # unlink first
    unlink_facebook_user(user, False)

    # link
    try:
        la = LinkedFacebookAccount(user=user, facebook_id=fb_user['id'], access_token=long_lived_token['access_token'],
                                   expires=long_lived_token['expires'])
        la.save()
    except Exception, e:
        # todo: log_error
        raise ValidationError({'error': "could not link facebook account"})


def unlink_facebook_user(user, strict=True):
    """
    Deleted the user's LinkedFacebookAccount
    """
    try:
        linked_account = LinkedFacebookAccount.objects.get(user=user)
    except LinkedFacebookAccount.DoesNotExist:
        if strict:
            raise ValidationError({'error': "no facebook account to unlink"})
    else:
        # todo: unlink from facebook services
        linked_account.delete()
