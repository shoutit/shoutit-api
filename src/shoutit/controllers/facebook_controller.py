# -*- coding: utf-8 -*-
"""

"""
from __future__ import unicode_literals

import datetime
import json
import urlparse

import requests
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.db.backends.postgresql_psycopg2.base import IntegrityError
from rest_framework.exceptions import ValidationError

from shoutit.api.v2.exceptions import FB_LINK_ERROR_TRY_AGAIN, FB_LINK_ERROR_EMAIL, FB_LINK_ERROR_NO_LINK
from shoutit.controllers import location_controller, user_controller
from shoutit.models import LinkedFacebookAccount
from shoutit.utils import debug_logger, now_plus_delta, error_logger


def user_from_facebook_auth_response(auth_response, initial_user=None, is_test=False):
    if 'accessToken' in auth_response:
        facebook_access_token = auth_response.get('accessToken')
    else:
        facebook_access_token = auth_response
    fb_user = fb_user_from_facebook_access_token(facebook_access_token)
    facebook_id = fb_user.get('id')
    try:
        linked_account = LinkedFacebookAccount.objects.get(facebook_id=facebook_id)
        user = linked_account.user
        if initial_user and initial_user.get('location'):
            location_controller.update_profile_location(user.profile, initial_user.get('location'))
    except ObjectDoesNotExist:
        debug_logger.debug('LinkedFacebookAccount.DoesNotExist for facebook_id %s.' % facebook_id)
        if 'email' not in fb_user:
            debug_logger.error('Facebook user has no email: %s' % json.dumps(fb_user))
            detail = FB_LINK_ERROR_EMAIL.detail
            detail.update({'fb_user': fb_user})
            raise ValidationError(detail)
        user = user_controller.auth_with_facebook(fb_user, facebook_access_token, initial_user, is_test)
        try:
            create_linked_facebook_account(user, facebook_access_token)
        except IntegrityError as e:
            error_logger.warn(str(e), exc_info=True)
            raise FB_LINK_ERROR_TRY_AGAIN

    return user


# todo: check!
def exchange_code(request, code):
    # Get Access Token using the Code then make an authResponse
    try:
        qs = request.META['QUERY_STRING'].split('&code')[0]
        # redirect_uri = urllib.quote('%s%s?%s' % (settings.SITE_LINK, request.path[1:], qs))
        redirect_uri = settings.SITE_LINK + request.path[1:] + qs
        exchange_url = 'https://graph.facebook.com/oauth/access_toke'
        params = {
            'client_id': settings.FACEBOOK_APP_ID,
            'client_secret': settings.FACEBOOK_APP_SECRET,
            'redirect_uri': redirect_uri,
            'code': code
        }
        response = requests.get(exchange_url, params=params, timeout=20)
        params = dict(urlparse.parse_qsl(response.content))
    except Exception, e:
        print e.message
        return None

    auth_response = {
        'accessToken': params['access_token'],
        'expiresIn': params['expires'],
    }
    return auth_response


def extend_token(short_lived_token):
    exchange_url = 'https://graph.facebook.com/oauth/access_token'
    params = {
        'client_id': settings.FACEBOOK_APP_ID,
        'client_secret': settings.FACEBOOK_APP_SECRET,
        'grant_type': "fb_exchange_token",
        'fb_exchange_token': short_lived_token
    }
    try:
        response = requests.get(exchange_url, params=params, timeout=20)
        if response.status_code != 200:
            raise ValueError("Invalid access token: %s" % response.content)
        response_params = dict(urlparse.parse_qsl(response.content))
        access_token = response_params.get('access_token')
        expires = response_params.get('expires')
        if not any((access_token, expires)):
            raise ValueError('access_token or expires not in response: %s' % response.content)
    except (requests.RequestException, ValueError) as e:
        debug_logger.error("Facebook token extend error: %s" % str(e))
        raise FB_LINK_ERROR_TRY_AGAIN
    return response_params


def debug_token(facebook_token):
    debug_url = 'https://graph.facebook.com/debug_token'
    params = {
        'access_token': "%s|%s" % (settings.FACEBOOK_APP_ID, settings.FACEBOOK_APP_SECRET),
        'input_token': facebook_token
    }
    try:
        response = requests.get(debug_url, params=params, timeout=20)
        if response.status_code != 200:
            raise ValueError("Invalid access token: %s" % response.content)
        return response.json()['data']
    except (requests.RequestException, ValueError, KeyError) as e:
        debug_logger.error("Facebook debug token error: %s" % str(e))
        raise FB_LINK_ERROR_TRY_AGAIN


def link_facebook_account(user, facebook_access_token):
    """
    Add LinkedFacebookAccount to user
    """
    fb_user = fb_user_from_facebook_access_token(facebook_access_token)
    facebook_id = fb_user.get('id')

    # check if the facebook account is already linked
    try:
        la = LinkedFacebookAccount.objects.get(facebook_id=facebook_id)
        debug_logger.error('User %s tried to link already linked facebook account id: %s.' % (user, facebook_id))
        if la.user == user:
            raise ValidationError({'error': "Facebook account is already linked to your profile."})
        raise ValidationError({'error': "Facebook account is already linked to somebody else's profile."})
    except LinkedFacebookAccount.DoesNotExist:
        pass

    # unlink previous facebook account
    unlink_facebook_user(user, False)

    # link
    # todo: get info, pic, etc about user
    try:
        create_linked_facebook_account(user, facebook_access_token)
    except IntegrityError as e:
        debug_logger.error("LinkedFacebookAccount creation error: %s." % str(e))
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
            debug_logger.error("User: %s, tried to unlink non-existing facebook account." % user)
            raise FB_LINK_ERROR_NO_LINK
    else:
        # todo: unlink from facebook services
        linked_account.delete()


def fb_user_from_facebook_access_token(facebook_access_token):
    graph_url = 'https://graph.facebook.com/me'
    params = {'access_token': facebook_access_token}
    try:
        fb_user = requests.get(graph_url, params=params, timeout=20).json()
        return fb_user
    except (requests.RequestException, ValueError) as e:
        debug_logger.error("Facebook Graph error: %s" % str(e))
        raise FB_LINK_ERROR_TRY_AGAIN


def create_linked_facebook_account(user, access_token):
    token_data = debug_token(access_token)
    expires_at = datetime.datetime.fromtimestamp(float(token_data.get('expires_at')))
    if abs((datetime.datetime.today() - expires_at).days) < 30:
        long_lived_token = extend_token(access_token)
        access_token = long_lived_token.get('access_token')
        expires = long_lived_token.get('expires')
        expires_at = now_plus_delta(datetime.timedelta(seconds=int(expires)))
    facebook_id = token_data.get('user_id')
    scopes = token_data.get('scopes')
    LinkedFacebookAccount.create(user=user, facebook_id=facebook_id, access_token=access_token, scopes=scopes,
                                 expires_at=expires_at)


def update_linked_facebook_account_scopes(facebook_user_id):
    try:
        la = LinkedFacebookAccount.objects.get(facebook_id=facebook_user_id)
        token_data = debug_token(la.access_token)
        scopes = token_data.get('scopes')
        la.scopes = scopes
        la.save(update_fields=['scopes'])
    except LinkedFacebookAccount.DoesNotExist as e:
        debug_logger.error("LinkedFacebookAccount for facebook id: %s does not exist" % str(e))


def delete_linked_facebook_account(facebook_user_id):
    try:
        LinkedFacebookAccount.objects.filter(facebook_id=facebook_user_id).delete()
    except IntegrityError as e:
        debug_logger.info("LinkedFacebookAccount deletion error: %s." % str(e), exc_info=True)
