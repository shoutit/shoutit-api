# -*- coding: utf-8 -*-
"""

"""
from __future__ import unicode_literals

import datetime
import json
from urllib import parse

import requests
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from django_rq import job
from pydash import objects

from common.utils import utcfromtimestamp
from shoutit.api.v3.exceptions import ShoutitBadRequest
from shoutit.controllers import location_controller, user_controller, notifications_controller, media_controller
from shoutit.models import LinkedFacebookAccount
from shoutit.models.auth import LinkedFacebookPage
from shoutit.utils import debug_logger, now_plus_delta, error_logger

FB_APP_ACCESS_TOKEN = '%s|%s' % (settings.FACEBOOK_APP_ID, settings.FACEBOOK_APP_SECRET)
FB_GRAPH_URL = 'https://graph.facebook.com/v2.6'
FB_GRAPH_ACCESS_TOKEN_URL = 'https://graph.facebook.com/oauth/access_token'

FB_LINK_ERROR_TRY_AGAIN = _("Could not link Facebook account, try again later")
FB_ERROR_TRY_AGAIN = _("Facebook error, try again later")
FB_LINK_ERROR_EMAIL = _("Could not access your email, make sure you allowed it")
FB_LINK_ERROR_NO_LINK = _("No Facebook account to unlink")

SIXTY_DAYS = 60 * 60 * 24 * 60


def user_from_facebook_auth_response(auth_response, initial_user=None, is_test=False):
    if 'accessToken' in auth_response:
        facebook_access_token = auth_response['accessToken']
    else:
        facebook_access_token = auth_response
    fb_user = fb_user_from_facebook_access_token(facebook_access_token)
    facebook_id = fb_user['id']
    try:
        linked_facebook = LinkedFacebookAccount.objects.filter(facebook_id=facebook_id).select_related(
            'user__profile').first()
        if not linked_facebook:
            raise LinkedFacebookAccount.DoesNotExist()
        save_linked_facebook(linked_facebook.user, facebook_access_token, fb_user, linked_facebook=linked_facebook)
        user = linked_facebook.user
        location = initial_user and initial_user.get('location')
        if location:
            location_controller.update_profile_location(user.ap, location)
    except LinkedFacebookAccount.DoesNotExist:
        debug_logger.debug('LinkedFacebookAccount.DoesNotExist for facebook_id %s' % facebook_id)
        if 'email' not in fb_user:
            dev_msg = 'Facebook user has no email: %s' % json.dumps(fb_user)
            debug_logger.error(dev_msg)
            raise ShoutitBadRequest(message=FB_LINK_ERROR_EMAIL, developer_message=dev_msg)
        user = user_controller.auth_with_facebook(fb_user, initial_user, is_test)
        try:
            save_linked_facebook(user, facebook_access_token, fb_user)
        except (ValidationError, IntegrityError) as e:
            raise ShoutitBadRequest(message=FB_LINK_ERROR_TRY_AGAIN, developer_message=str(e))

    return user


def facebook_graph_object(graph_path, params):
    graph_url = FB_GRAPH_URL + graph_path
    try:
        response = requests.get(graph_url, params=params, timeout=20)
        response_data = response.json()
        error = response_data.get('error')
        if response.status_code != 200 or error:
            dev_msg = error.get('message') if isinstance(error, dict) else str(response_data)
            dev_msg = "Facebook Graph error: %s" % dev_msg
            raise ShoutitBadRequest(message=FB_ERROR_TRY_AGAIN, developer_message=dev_msg)
        return response_data
    except requests.RequestException as e:
        dev_msg = "Facebook Graph error: %s" % str(e)
        debug_logger.error(dev_msg)
        raise ShoutitBadRequest(message=FB_ERROR_TRY_AGAIN, developer_message=dev_msg)


def debug_token(facebook_token):
    params = {
        'access_token': FB_APP_ACCESS_TOKEN,
        'input_token': facebook_token
    }
    token = facebook_graph_object('/debug_token', params)
    return token['data']


def fb_user_from_facebook_access_token(facebook_access_token):
    params = {
        'fields': "id,email,name,first_name,last_name,gender,birthday,picture.width(1000),cover,friends",
        'access_token': facebook_access_token
    }
    fb_user = facebook_graph_object('/me', params)
    return fb_user


def fb_page_from_facebook_page_id(facebook_page_id, facebook_access_token):
    params = {
        'fields': 'access_token,category,name,id,perms',
        'access_token': facebook_access_token
    }
    accounts = facebook_graph_object('/me/accounts', params)['data']
    for account in accounts:
        if account['id'] == facebook_page_id:
            return account
    raise ShoutitBadRequest(_("Couldn't find the specified Facebook Page"))


def extend_token(short_lived_token):
    exchange_url = FB_GRAPH_ACCESS_TOKEN_URL
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
        response_params = dict(parse.parse_qsl(response.content.decode()))
        access_token = response_params.get('access_token')
        if not access_token:
            raise ValueError('`access_token` not in response: %s' % response.content)
        expires = response_params.get('expires')
        # Sometimes Facebook doesn't return expiry, assume 60 days
        response_params['expires'] = expires or SIXTY_DAYS
    except (requests.RequestException, ValueError) as e:
        debug_logger.error("Facebook token extend error: %s" % str(e))
        raise ShoutitBadRequest(message=FB_ERROR_TRY_AGAIN, developer_message=str(e))
    return response_params


def link_facebook_account(user, facebook_access_token):
    """
    Add LinkedFacebookAccount to user
    """
    fb_user = fb_user_from_facebook_access_token(facebook_access_token)
    facebook_id = fb_user['id']
    linked_page_ids = []

    # Check whether the Facebook account is already linked
    try:
        la = LinkedFacebookAccount.objects.get(facebook_id=facebook_id)
        debug_logger.warning('User %s tried to link already linked facebook account id: %s.' % (user, facebook_id))
        if la.user != user:
            raise ShoutitBadRequest(_("Facebook account is already linked to somebody else's profile"))
        linked_page_ids = list(la.pages.values_list('facebook_id', flat=True))  # copy the list
    except LinkedFacebookAccount.DoesNotExist:
        pass

    # Unlink previous Facebook account
    unlink_facebook_user(user, strict=False)

    # Link Facebook account
    try:
        linked_facebook = save_linked_facebook(user, facebook_access_token, fb_user)
    except (ValidationError, IntegrityError) as e:
        debug_logger.error("LinkedFacebookAccount creation error: %s" % str(e))
        raise ShoutitBadRequest(message=FB_LINK_ERROR_TRY_AGAIN, developer_message=str(e))

    # Link Facebook Pages if any existed in the previous LinkedFacebookAccount
    for facebook_page_id in linked_page_ids:
        link_facebook_page(linked_facebook, facebook_page_id)

    # Activate the user if not yet activated
    if not user.is_activated:
        user.notify = False
        user.activate()


def unlink_facebook_user(user, strict=True):
    """
    Deleted the user's LinkedFacebookAccount
    """
    linked_account = LinkedFacebookAccount.objects.filter(user=user)
    if linked_account.exists():
        linked_account.delete()
    elif strict:
        debug_logger.warning("User: %s, tried to unlink non-existing facebook account" % user)
        raise ShoutitBadRequest(FB_LINK_ERROR_NO_LINK)


def save_linked_facebook(user, access_token, fb_user, linked_facebook=None):
    token_data = debug_token(access_token)
    expires_at = token_data['expires_at']
    if expires_at == 0:
        expires_at = timezone.now() + datetime.timedelta(days=60)
    else:
        expires_at = utcfromtimestamp(float(expires_at))
    if abs((timezone.now() - expires_at).days) < 30:
        long_lived_token = extend_token(access_token)
        access_token = long_lived_token['access_token']
        expires = long_lived_token['expires']
        expires_at = now_plus_delta(seconds=int(expires))
    facebook_id = token_data['user_id']
    name = fb_user['name']
    scopes = token_data['scopes']
    friends_data = objects.get(fb_user, 'friends.data') or []
    friends = [f['id'] for f in friends_data]
    if linked_facebook:
        linked_facebook.update(user=user, facebook_id=facebook_id, name=name, access_token=access_token, scopes=scopes,
                               expires_at=expires_at, friends=friends)
    else:
        linked_facebook = LinkedFacebookAccount.create(user=user, facebook_id=facebook_id, access_token=access_token,
                                                       scopes=scopes, expires_at=expires_at, friends=friends, name=name)

    if hasattr(user, 'profile'):
        update_profile_using_fb_user(user.profile, fb_user)
    return linked_facebook


def update_linked_facebook_account_scopes(facebook_user_id):
    try:
        la = LinkedFacebookAccount.objects.get(facebook_id=facebook_user_id)
    except LinkedFacebookAccount.DoesNotExist:
        debug_logger.error("LinkedFacebookAccount for facebook id: %s does not exist" % facebook_user_id)
    else:
        try:
            token_data = debug_token(la.access_token)
        except ShoutitBadRequest:
            la.delete()
            debug_logger.error("LinkedFacebookAccount for facebook id: %s is expired. Deleting it" % facebook_user_id)
        else:
            scopes = token_data['scopes']
            la.scopes = scopes
            la.save(update_fields=['scopes'])

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


def update_profile_using_fb_user(profile, fb_user):
    # Todo (mo): Update `gender`, `birthday`, ?

    # Image
    if not profile.image:
        image_url = objects.get(fb_user, 'picture.data.url')
        is_silhouette = objects.get(fb_user, 'picture.data.is_silhouette')
        if image_url and is_silhouette is False:
            media_controller.set_profile_media(profile, 'image', url=image_url)

    # Cover
    if not profile.cover:
        cover_source = objects.get(fb_user, 'cover.source')
        if cover_source:
            media_controller.set_profile_media(profile, 'cover', url=cover_source)


def link_facebook_page(linked_facebook, facebook_page_id):
    """
    Add FacebookPage to LinkedFacebookAccount
    """
    facebook_page = fb_page_from_facebook_page_id(facebook_page_id, linked_facebook.access_token)
    defaults = {'access_token': facebook_page['access_token'], 'category': facebook_page['category'],
                'name': facebook_page['name'], 'perms': facebook_page['perms']}
    LinkedFacebookPage.objects.update_or_create(linked_facebook=linked_facebook, facebook_id=facebook_page_id,
                                                defaults=defaults)


def unlink_facebook_page(linked_facebook, facebook_page_id):
    """
    Remove FacebookPage from LinkedFacebookAccount
    """
    LinkedFacebookPage.objects.filter(linked_facebook=linked_facebook, facebook_id=facebook_page_id).delete()


@job(settings.RQ_QUEUE)
def pre_cache_graph(url):
    params = {
        'id': url,
        'scrape': True,
        'access_token': FB_APP_ACCESS_TOKEN
    }
    return requests.post(FB_GRAPH_URL, params=params).json()


# todo: check!
def exchange_code(request, code):
    # Get Access Token using the Code then make an authResponse
    try:
        qs = request.META['QUERY_STRING'].split('&code')[0]
        # redirect_uri = urllib.quote('%s%s?%s' % (settings.SITE_LINK, request.path[1:], qs))
        redirect_uri = settings.SITE_LINK + request.path[1:] + qs
        exchange_url = FB_GRAPH_ACCESS_TOKEN_URL
        params = {
            'client_id': settings.FACEBOOK_APP_ID,
            'client_secret': settings.FACEBOOK_APP_SECRET,
            'redirect_uri': redirect_uri,
            'code': code
        }
        response = requests.get(exchange_url, params=params, timeout=20)
        params = dict(parse.parse_qsl(response.content))
    except Exception as e:
        error_logger.warn(e)
        return None

    auth_response = {
        'accessToken': params['access_token'],
        'expiresIn': params['expires'],
    }
    return auth_response


def parse_signed_request(signed_request='a.a', secret=settings.FACEBOOK_APP_SECRET):
    import hashlib
    import hmac

    l = signed_request.split('.', 2)
    encoded_sig = l[0]
    payload = l[1]
    sig = base64_url_decode(encoded_sig)
    data = json.loads(base64_url_decode(payload))
    if data['algorithm'].upper() != 'HMAC-SHA256':
        return {}

    # http://stackoverflow.com/questions/20849805/python-hmac-typeerror-character-mapping-must-return-integer-none-or-unicode
    expected_sig = hmac.new(str(secret), msg=str(payload), digestmod=hashlib.sha256).digest()
    if sig != expected_sig:
        return {}

    return data


def base64_url_decode(inp):
    import base64

    inp = inp.replace('-', '+').replace('_', '/')
    padding_factor = (4 - len(inp) % 4) % 4
    inp += "=" * padding_factor
    return base64.decodestring(inp)
