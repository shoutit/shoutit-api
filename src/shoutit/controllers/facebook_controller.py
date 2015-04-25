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
from django.db.backends.postgresql_psycopg2.base import IntegrityError
from rest_framework.exceptions import ValidationError
from shoutit.api.v2.exceptions import (FB_LINK_ERROR_TRY_AGAIN, FB_LINK_ERROR_EMAIL,
                                       FB_LINK_ERROR_NO_LINK)

from shoutit.models import LinkedFacebookAccount
from shoutit.controllers.user_controller import auth_with_facebook, update_profile_location
import logging
logger = logging.getLogger('shoutit')


def user_from_facebook_auth_response(auth_response, initial_user=None):
    if 'accessToken' in auth_response:
        access_token = auth_response.get('accessToken')
    else:
        access_token = auth_response
    fb_user = fb_user_from_facebook_access_token(access_token)
    facebook_id = fb_user.get('id')

    try:
        linked_account = LinkedFacebookAccount.objects.get(facebook_id=facebook_id)
        user = linked_account.user
    except ObjectDoesNotExist:
        logger.debug('LinkedGoogleAccount.DoesNotExist for facebook_id %s creating new user.' % facebook_id)
        if 'email' not in fb_user:
            logger.error('Facebook user has no email: %s' % json.dumps(fb_user))
            raise FB_LINK_ERROR_EMAIL
        long_lived_token = extend_token(access_token)
        user = auth_with_facebook(fb_user, long_lived_token)

    if initial_user and initial_user.get('location'):
        update_profile_location(user.profile, initial_user['location'])
    return user


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
    query = "client_id={}&client_secret={}&grant_type=fb_exchange_token&fb_exchange_token={}"
    query = query.format(settings.FACEBOOK_APP_ID, settings.FACEBOOK_APP_SECRET, short_lived_token)
    exchange_url = 'https://graph.facebook.com/oauth/access_token?{}'.format(query)
    try:
        response = urllib2.urlopen(exchange_url, timeout=20)
        params = dict(urlparse.parse_qsl(response.read()))
        if not ('access_token' in params and 'expires' in params):
            raise Exception('access_token or expires not in params: {}'.format(json.dumps(params)))
    except Exception, e:
        logger.error("Facebook token extend error: %s" % str(e))
        raise FB_LINK_ERROR_TRY_AGAIN

    return {'access_token': params.get('access_token'), 'expires': params.get('expires')}


def link_facebook_account(user, facebook_access_token):
    """
    Add LinkedFacebookAccount to user
    """
    fb_user = fb_user_from_facebook_access_token(facebook_access_token)
    facebook_id = fb_user.get('id')

    # check if the facebook account is already linked
    try:
        la = LinkedFacebookAccount.objects.get(facebook_id=facebook_id)
        logger.error('User %s tried to link already linked facebook account id: %s.' % (user, facebook_id))
        if la.user == user:
            raise ValidationError({'error': "Facebook account is already linked to your profile."})
        raise ValidationError({'error': "Facebook account is already linked to somebody else's "
                                        "profile."})
    except LinkedFacebookAccount.DoesNotExist:
        pass

    # unlink previous facebook account
    unlink_facebook_user(user, False)

    # link
    # todo: get info, pic, etc about user
    long_lived_token = extend_token(facebook_access_token)
    access_token = long_lived_token.get('access_token')
    expires = long_lived_token.get('expires')
    try:
        la = LinkedFacebookAccount(user=user, facebook_id=facebook_id, expires=expires,
                                   access_token=access_token)
        la.save()
    except (ValidationError, IntegrityError) as e:
        logger.error("LinkedFacebookAccount creation error: %s." % str(e))
        raise FB_LINK_ERROR_TRY_AGAIN

    # activate the user
    user.activate()


def unlink_facebook_user(user, strict=True):
    """
    Deleted the user's LinkedFacebookAccount
    """
    try:
        linked_account = LinkedFacebookAccount.objects.get(user=user)
    except LinkedFacebookAccount.DoesNotExist:
        if strict:
            logger.error("User: %s, tried to unlink non-existing facebook account." % user)
            raise FB_LINK_ERROR_NO_LINK
    else:
        # todo: unlink from facebook services
        linked_account.delete()


def fb_user_from_facebook_access_token(facebook_access_token):
    graph_url = 'https://graph.facebook.com/me?access_token={}'.format(facebook_access_token)
    try:
        response = urllib2.urlopen(graph_url, timeout=20)
        fb_user = json.loads(response.read())
        return fb_user
    except (urllib2.HTTPError, ValueError) as e:
        logger.error("Facebook Graph error: %s" % str(e))
        raise FB_LINK_ERROR_TRY_AGAIN
