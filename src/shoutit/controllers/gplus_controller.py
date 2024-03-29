# -*- coding: utf-8 -*-
"""

"""
import json

import httplib2
from apiclient import discovery
from django.conf import settings
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import IntegrityError
from django.utils.translation import ugettext_lazy as _
from oauth2client.client import (AccessTokenRefreshError, FlowExchangeError, credentials_from_clientsecrets_and_code,
                                 OOB_CALLBACK_URN)

from shoutit.api.v3.exceptions import ShoutitBadRequest
from shoutit.controllers import user_controller, location_controller
from shoutit.models import LinkedGoogleAccount
from shoutit.utils import debug_logger

GPLUS_LINK_ERROR_EMAIL = _("Could not access your email, make sure you allowed it")
GPLUS_LINK_ERROR_NO_LINK = _("No Google account to unlink")
GPLUS_LINK_ERROR_TRY_AGAIN = _("Could not access your Google account, try again later")


# Todo: Compare with user_from_facebook_auth_response, check why linking is not happening here
def user_from_gplus_code(gplus_code, initial_user=None, client=None, is_test=False):
    debug_logger.debug('user_from_gplus_code')
    credentials = credentials_from_code_and_client(gplus_code, client)
    gplus_id = credentials.id_token.get('sub')
    try:
        linked_account = LinkedGoogleAccount.objects.get(gplus_id=gplus_id)
        user = linked_account.user
        if initial_user and initial_user.get('location'):
            location_controller.update_profile_location(user.ap, initial_user.get('location'))
    except LinkedGoogleAccount.DoesNotExist:
        debug_logger.debug('LinkedGoogleAccount.DoesNotExist for gplus_id %s.' % gplus_id)
        try:
            # Create a new authorized API client.
            http = httplib2.Http()
            http = credentials.authorize(http)
            # Get the logged gplus user.
            service = discovery.build("plus", "v1", http=http)
            gplus_user = service.people().get(userId='me').execute()
            email = gplus_user.get('emails')[0].get('value')
            if not email:
                dev_msg = 'Google user has no email: %s' % json.dumps(gplus_user)
                debug_logger.error(dev_msg)
                raise ShoutitBadRequest(message=GPLUS_LINK_ERROR_EMAIL, developer_message=dev_msg)
        except AccessTokenRefreshError as e:
            debug_logger.error("Calling service.people() error: AccessTokenRefreshError")
            raise ShoutitBadRequest(message=GPLUS_LINK_ERROR_TRY_AGAIN, developer_message=str(e))
        except Exception as e:
            dev_msg = "Calling service.people() error: %s" % str(e)
            debug_logger.error(dev_msg)
            raise ShoutitBadRequest(message=GPLUS_LINK_ERROR_TRY_AGAIN, developer_message=dev_msg)
        user = user_controller.auth_with_gplus(gplus_user, credentials, initial_user, is_test)

    return user


def link_gplus_account(user, gplus_code, client=None):
    """
    Add LinkedGoogleAccount to user
    """
    credentials = credentials_from_code_and_client(gplus_code, client)
    gplus_id = credentials.id_token.get('sub')

    # Check whether the Google account is already linked
    try:
        la = LinkedGoogleAccount.objects.get(gplus_id=gplus_id)
        debug_logger.warning('User %s tried to link already linked gplus account id: %s.' % (user, gplus_id))
        if la.user != user:
            raise ShoutitBadRequest(_("This Google account is already linked to somebody else's profile"))
    except LinkedGoogleAccount.DoesNotExist:
        pass

    # Unlink previous Google account
    unlink_gplus_user(user, False)

    # Link Google account
    # todo: get info, pic, etc about user
    try:
        LinkedGoogleAccount.objects.create(user=user, credentials_json=credentials.to_json(), gplus_id=gplus_id)
    except (DjangoValidationError, IntegrityError) as e:
        debug_logger.error("LinkedGoogleAccount creation error: %s" % str(e))
        raise ShoutitBadRequest(GPLUS_LINK_ERROR_TRY_AGAIN)

    # Activate the user if not yet activated
    if not user.is_activated:
        user.notify = False
        user.activate()


def unlink_gplus_user(user, strict=True, notify=True):
    """
    Deleted the user's LinkedGoogleAccount
    """
    try:
        linked_account = LinkedGoogleAccount.objects.get(user=user)
    except LinkedGoogleAccount.DoesNotExist:
        if strict:
            debug_logger.warning("User: %s, tried to unlink non-existing gplus account" % user)
            raise ShoutitBadRequest(GPLUS_LINK_ERROR_NO_LINK)
    else:
        # todo: unlink from google services
        linked_account.delete()


def redirect_uri_from_client(client='shoutit-test'):
    if hasattr(client, 'name'):
        client = client.name
    if client in ['shoutit-android', 'shoutit-ios']:
        redirect_uri = OOB_CALLBACK_URN
    elif client == 'shoutit-web':
        redirect_uri = 'postmessage'
    elif client == 'shoutit-test':
        redirect_uri = 'https://developers.google.com/oauthplayground'
    else:
        raise ShoutitBadRequest(message=GPLUS_LINK_ERROR_TRY_AGAIN,
                                developer_message="Invalid API client '%s'" % client)
    debug_logger.debug("client: %s, redirect_uri: %s" % (client, redirect_uri))
    return redirect_uri


def credentials_from_code_and_client(code, client):
    redirect_uri = redirect_uri_from_client(client)
    try:
        # Upgrade the authorization code into a credentials object
        credentials = credentials_from_clientsecrets_and_code(filename=settings.GOOGLE_WEB_CLIENT, scope='', code=code,
                                                              redirect_uri=redirect_uri)
        return credentials
    except FlowExchangeError as e:
        dev_msg = "FlowExchangeError: %s" % str(e)
        debug_logger.error(dev_msg)
        raise ShoutitBadRequest(message=GPLUS_LINK_ERROR_TRY_AGAIN, developer_message=dev_msg)
