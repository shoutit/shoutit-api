import urllib2
import json
from apps.shoutit.controllers.user_controller import auth_with_gplus, login_without_password
from apps.shoutit.models import LinkedGoogleAccount
from django.core.exceptions import ObjectDoesNotExist
from apiclient.discovery import build
import httplib2
from oauth2client.client import AccessTokenRefreshError
from oauth2client.client import credentials_from_code, Credentials
from oauth2client.client import FlowExchangeError
import apps.shoutit.settings as Settings

# TODO: this requires established external connection, try catch would handle it better.
SERVICE = build('plus', 'v1')


def user_from_gplus_code(request, code):

    try:
        # Upgrade the authorization code into a credentials object
        credentials = credentials_from_code(Settings.GOOGLE_APP_CLIENT_ID, Settings.GOOGLE_APP_CLIENT_SECRET, '', code)
    except FlowExchangeError:
        return None

    gplus_id = credentials.id_token['sub']
    try:
        linked_account = LinkedGoogleAccount.objects.get(gplus_id=gplus_id)
        user = linked_account.user
    except ObjectDoesNotExist:
        user = None

    if not user:
        try:
            # Create a new authorized API client.
            http = httplib2.Http()
            http = credentials.authorize(http)
            # Get the logged gplus user.
            google_request = SERVICE.people().get(userId='me')
            gplus_user = google_request.execute(http=http)
        except AccessTokenRefreshError:
            return None

        user = auth_with_gplus(request, gplus_user, credentials)

    if user:
        login_without_password(request, user)
        request.session['user_renew_location'] = True
        return user
    else:
        return None
