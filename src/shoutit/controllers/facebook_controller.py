# -*- coding: utf-8 -*-
"""

"""
from __future__ import unicode_literals

import datetime
import json
import urlparse

import requests
from django.conf import settings
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import IntegrityError
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from common.utils import utcfromtimestamp
from shoutit.api.v3.exceptions import ShoutitBadRequest
from shoutit.controllers import location_controller, user_controller, notifications_controller
from shoutit.models import LinkedFacebookAccount
from shoutit.utils import debug_logger, now_plus_delta, error_logger

FB_LINK_ERROR_TRY_AGAIN = "Could not link Facebook account, try again later."
FB_LINK_ERROR_EMAIL = "Could not access user email, make sure you allowed it."
FB_LINK_ERROR_NO_LINK = "No Facebook account to unlink."


def user_from_facebook_auth_response(auth_response, initial_user=None, is_test=False):
    if 'accessToken' in auth_response:
        facebook_access_token = auth_response.get('accessToken')
    else:
        facebook_access_token = auth_response
    fb_user = fb_user_from_facebook_access_token(facebook_access_token)
    facebook_id = fb_user.get('id')
    try:
        linked_account = LinkedFacebookAccount.objects.get(facebook_id=facebook_id)
        save_linked_facebook_account(linked_account.user, facebook_access_token, linked_account, fb_user)
        user = linked_account.user
        if initial_user and initial_user.get('location'):
            location_controller.update_profile_location(user.profile, initial_user.get('location'))
    except LinkedFacebookAccount.DoesNotExist:
        debug_logger.debug('LinkedFacebookAccount.DoesNotExist for facebook_id %s.' % facebook_id)
        if 'email' not in fb_user:
            dev_msg = 'Facebook user has no email: %s' % json.dumps(fb_user)
            debug_logger.error(dev_msg)
            raise ShoutitBadRequest(message=FB_LINK_ERROR_EMAIL, developer_message=dev_msg)
        user = user_controller.auth_with_facebook(fb_user, facebook_access_token, initial_user, is_test)
        try:
            save_linked_facebook_account(user, facebook_access_token, fb_user=fb_user)
        except (DjangoValidationError, IntegrityError) as e:
            raise ShoutitBadRequest(message=FB_LINK_ERROR_TRY_AGAIN, developer_message=str(e))

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
    except Exception as e:
        error_logger.warn(e.message)
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
            raise ValueError('`access_token` or `expires` not in response: %s' % response.content)
    except (requests.RequestException, ValueError) as e:
        debug_logger.error("Facebook token extend error: %s" % str(e))
        raise ShoutitBadRequest(message=FB_LINK_ERROR_TRY_AGAIN, developer_message=str(e))
    return response_params


def debug_token(facebook_token):
    debug_url = 'https://graph.facebook.com/debug_token'
    params = {
        'access_token': "%s|%s" % (settings.FACEBOOK_APP_ID, settings.FACEBOOK_APP_SECRET),
        'input_token': facebook_token
    }
    try:
        response = requests.get(debug_url, params=params, timeout=20)
        response_data = response.json()
        error = response_data.get('error')
        if response.status_code != 200 or error:
            dev_msg = error.get('message') if isinstance(error, dict) else str(response_data)
            dev_msg = "Facebook debug token error: %s" % dev_msg
            raise ShoutitBadRequest(message=FB_LINK_ERROR_TRY_AGAIN, developer_message=dev_msg)
        return response_data['data']
    except requests.RequestException as e:
        dev_msg = "Facebook debug token error: %s" % str(e)
        debug_logger.error(dev_msg)
        raise ShoutitBadRequest(message=FB_LINK_ERROR_TRY_AGAIN, developer_message=dev_msg)


def link_facebook_account(user, facebook_access_token):
    """
    Add LinkedFacebookAccount to user
    """
    fb_user = fb_user_from_facebook_access_token(facebook_access_token)
    facebook_id = fb_user.get('id')

    # check if the facebook account is already linked
    try:
        la = LinkedFacebookAccount.objects.get(facebook_id=facebook_id)
        debug_logger.warning('User %s tried to link already linked facebook account id: %s.' % (user, facebook_id))
        if la.user != user:
            raise ShoutitBadRequest("Facebook account is already linked to somebody else's profile.")
    except LinkedFacebookAccount.DoesNotExist:
        pass

    # unlink previous facebook account
    unlink_facebook_user(user, strict=False, notify=False)

    # link
    # Todo: get info, pic, etc about user
    try:
        save_linked_facebook_account(user, facebook_access_token, fb_user=fb_user)
    except (DjangoValidationError, IntegrityError) as e:
        debug_logger.error("LinkedFacebookAccount creation error: %s." % str(e))
        raise ShoutitBadRequest(message=FB_LINK_ERROR_TRY_AGAIN, developer_message=str(e))

    # activate the user
    if not user.is_activated:
        user.notify = False
        user.activate()

    # Send `profile_update` on Pusher
    notifications_controller.notify_user_of_profile_update(user)


def unlink_facebook_user(user, strict=True, notify=True):
    """
    Deleted the user's LinkedFacebookAccount
    """
    linked_account = LinkedFacebookAccount.objects.filter(user=user)
    if linked_account.exists():
        linked_account.delete()
    elif strict:
        debug_logger.warning("User: %s, tried to unlink non-existing facebook account." % user)
        raise ShoutitBadRequest(FB_LINK_ERROR_NO_LINK)

    if notify:
        # Send `profile_update` on Pusher
        notifications_controller.notify_user_of_profile_update(user)


def fb_user_from_facebook_access_token(facebook_access_token):
    graph_url = 'https://graph.facebook.com/v2.6/me'
    params = {
        'fields': "id,email,first_name,last_name,gender,friends",
        'access_token': facebook_access_token
    }
    try:
        fb_user = requests.get(graph_url, params=params, timeout=20).json()
        return fb_user
    except (requests.RequestException, ValueError) as e:
        dev_msg = "Facebook Graph error: %s" % str(e)
        debug_logger.error(dev_msg)
        raise ShoutitBadRequest(message=FB_LINK_ERROR_TRY_AGAIN, developer_message=dev_msg)


def save_linked_facebook_account(user, access_token, la=None, fb_user=None):
    token_data = debug_token(access_token)
    expires_at = utcfromtimestamp(float(token_data.get('expires_at')))
    if abs((timezone.now() - expires_at).days) < 30:
        long_lived_token = extend_token(access_token)
        access_token = long_lived_token.get('access_token')
        expires = long_lived_token.get('expires')
        expires_at = now_plus_delta(datetime.timedelta(seconds=int(expires)))
    facebook_id = token_data.get('user_id')
    scopes = token_data.get('scopes')
    friends_data = fb_user.get('friends') if fb_user else None
    friends_data = friends_data['data'] if friends_data else None
    friends = map(lambda f: f['id'], friends_data) if friends_data else []
    if la:
        LinkedFacebookAccount.objects.filter(id=la.id).update(
            user=user, facebook_id=facebook_id, access_token=access_token, scopes=scopes, expires_at=expires_at,
            friends=friends)
    else:
        LinkedFacebookAccount.create(
            user=user, facebook_id=facebook_id, access_token=access_token, scopes=scopes, expires_at=expires_at,
            friends=friends)


def update_linked_facebook_account_scopes(facebook_user_id):
    try:
        la = LinkedFacebookAccount.objects.get(facebook_id=facebook_user_id)
    except LinkedFacebookAccount.DoesNotExist:
        debug_logger.error("LinkedFacebookAccount for facebook id: %s does not exist" % facebook_user_id)
    else:
        try:
            token_data = debug_token(la.access_token)
            scopes = token_data.get('scopes')
            la.scopes = scopes
            la.save(update_fields=['scopes'])
        except ValidationError:
            la.delete()
            debug_logger.error("LinkedFacebookAccount for facebook id: %s is expired. Deleting it." % facebook_user_id)

        # Send `profile_update` on Pusher
        notifications_controller.notify_user_of_profile_update(la.user)


def delete_linked_facebook_account(facebook_user_id):
    try:
        la = LinkedFacebookAccount.objects.get(facebook_id=facebook_user_id)
    except LinkedFacebookAccount.DoesNotExist:
        debug_logger.error("LinkedFacebookAccount for facebook id: %s does not exist" % facebook_user_id)
    else:
        # Delete LinkedFacebookAccount
        user = la.user
        la.delete()

        # Send `profile_update` on Pusher
        notifications_controller.notify_user_of_profile_update(user)
