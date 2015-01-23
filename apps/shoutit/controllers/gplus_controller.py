import httplib2
from oauth2client.client import AccessTokenRefreshError, FlowExchangeError
from oauth2client.client import credentials_from_clientsecrets_and_code, OOB_CALLBACK_URN
from django.conf import settings
from apps.shoutit.models import LinkedGoogleAccount
from apps.shoutit.controllers.user_controller import auth_with_gplus, login_without_password, update_profile_location


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
    except LinkedGoogleAccount.DoesNotExist:
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


def link_gplus_user(request, code):
    redirect_uri = 'postmessage'
    if hasattr(request, 'is_api') and request.is_api:
        redirect_uri = OOB_CALLBACK_URN

    try:
        # Upgrade the authorization code into a credentials object
        credentials = credentials_from_clientsecrets_and_code(filename=settings.GOOGLE_APP['CLIENTS'][settings.GOOGLE_APP_CLIENT_ID]['FILE']
                                                              , scope='', code=code, redirect_uri=redirect_uri)
    except FlowExchangeError as flowError:
        return flowError, False
    else:
        gplus_id = credentials.id_token['sub']

    # unlink first
    unlink_gplus_user(request)

    # link
    try:
        la = LinkedGoogleAccount(user=request.user, credentials_json=credentials.to_json(), gplus_id=gplus_id)
        la.save()
        return None, True
    except Exception, e:
        return e, False


def unlink_gplus_user(request):
    """
    Deleted the user's LinkedGoogleAccount
    :param request:
    :return:
    """
    try:
        linked_account = LinkedGoogleAccount.objects.get(user=request.user)
    except LinkedGoogleAccount.DoesNotExist:
        pass
    else:
        linked_account.delete()
