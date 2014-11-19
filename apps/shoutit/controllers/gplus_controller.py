from apps.shoutit.controllers.user_controller import auth_with_gplus, login_without_password, update_profile_location
from apps.shoutit.models import LinkedGoogleAccount
from django.core.exceptions import ObjectDoesNotExist
import httplib2
from oauth2client.client import AccessTokenRefreshError
from oauth2client.client import credentials_from_clientsecrets_and_code, OOB_CALLBACK_URN
from oauth2client.client import FlowExchangeError
from django.conf import settings


def user_from_gplus_code(request, code, initial_user=None):
    redirect_uri = 'postmessage'
    if hasattr(request, 'is_api') and request.is_api:
        redirect_uri = OOB_CALLBACK_URN

    try:
        # Upgrade the authorization code into a credentials object
        credentials = credentials_from_clientsecrets_and_code(filename=settings.GOOGLE_APP['CLIENTS'][settings.GOOGLE_APP_CLIENT_ID]['FILE']
                                                              , scope='', code=code, redirect_uri=redirect_uri)
    except FlowExchangeError as flowError:
        return flowError, None

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
            google_request = settings.GPLUS_SERVICE.people().get(userId='me')
            gplus_user = google_request.execute(http=http)
        except AccessTokenRefreshError, e:
            return e, None

        user = auth_with_gplus(request, gplus_user, credentials)

    if user:
        if initial_user and initial_user['location']:
            update_profile_location(user.profile, initial_user['location'])

        login_without_password(request, user)
        return None, user
    else:
        return Exception('Could not login the user'), None
