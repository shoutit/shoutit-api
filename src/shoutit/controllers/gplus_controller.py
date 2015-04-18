# -*- coding: utf-8 -*-
"""

"""
from __future__ import unicode_literals

import httplib2
from oauth2client.client import AccessTokenRefreshError, FlowExchangeError
from oauth2client.client import credentials_from_clientsecrets_and_code, OOB_CALLBACK_URN
from django.conf import settings
from apiclient import discovery
from rest_framework.exceptions import ValidationError

from shoutit.models import LinkedGoogleAccount
from shoutit.controllers.user_controller import auth_with_gplus, update_profile_location


def user_from_gplus_code(code, initial_user=None, client='shoutit-test'):
    print 'user_from_gplus_code'
    redirect_uri = OOB_CALLBACK_URN
    if client == 'shoutit-web':
        redirect_uri = 'postmessage'
    if client == 'shoutit-test':
        redirect_uri = 'https://developers.google.com/oauthplayground'
    print 'redirect_uri', redirect_uri

    try:
        # Upgrade the authorization code into a credentials object
        google_api_client = settings.GOOGLE_API['CLIENTS']['web']
        credentials = credentials_from_clientsecrets_and_code(filename=google_api_client['FILE'], scope='', code=code,
                                                              redirect_uri=redirect_uri)
    except FlowExchangeError as flowError:
        return flowError, None

    gplus_id = credentials.id_token['sub']

    try:
        linked_account = LinkedGoogleAccount.objects.get(gplus_id=gplus_id)
        user = linked_account.user
    except LinkedGoogleAccount.DoesNotExist:
        print 'LinkedGoogleAccount.DoesNotExist for gplus_id', gplus_id, 'creating new user'
        user = None

    if not user:
        try:
            # Create a new authorized API client.
            http = httplib2.Http()
            http = credentials.authorize(http)
            # Get the logged gplus user.
            service = discovery.build("plus", "v1", http=http)
            gplus_user = service.people().get(userId='me').execute()
        except AccessTokenRefreshError as e:
            print "calling service.people() error: AccessTokenRefreshError"
            return e, None
        except Exception as e:
            print "calling service.people() error: ", str(e)
            return e, None

        user = auth_with_gplus(gplus_user, credentials)

    if user:
        if initial_user and initial_user['location']:
            update_profile_location(user.profile, initial_user['location'])

        return None, user
    else:
        return Exception('Could not login the user'), None


def link_gplus_account(user, gplus_code, client=None):
    """
    Add LinkedGoogleAccount to user
    """
    redirect_uri = 'postmessage'
    if client and client.name in ['shoutit-ios', 'shoutit-android']:
        redirect_uri = OOB_CALLBACK_URN

    try:
        # Upgrade the authorization code into a credentials object
        google_api_client = settings.GOOGLE_API['CLIENTS']['web']
        credentials = credentials_from_clientsecrets_and_code(filename=google_api_client['FILE'], scope='', code=gplus_code,
                                                              redirect_uri=redirect_uri)
    except FlowExchangeError as flow_error:
        raise ValidationError({'gplus_code': str(flow_error)})
    else:
        gplus_id = credentials.id_token['sub']

    # unlink first
    unlink_gplus_user(user, False)

    # link
    try:
        la = LinkedGoogleAccount(user=user, credentials_json=credentials.to_json(), gplus_id=gplus_id)
        la.save()
    except Exception, e:
        # todo: log_error
        raise ValidationError({'error': "could not link gplus account"})


def unlink_gplus_user(user, strict=True):
    """
    Deleted the user's LinkedGoogleAccount
    """
    try:
        linked_account = LinkedGoogleAccount.objects.get(user=user)
    except LinkedGoogleAccount.DoesNotExist:
        if strict:
            raise ValidationError({'error': "no gplus account to unlink"})
    else:
        # todo: unlink from google services
        linked_account.delete()