"""

"""
import uuid

from django.utils.translation import ugettext_lazy as _
from rest_framework import HTTP_HEADER_ENCODING, exceptions
from rest_framework.authentication import BaseAuthentication, TokenAuthentication, SessionAuthentication
from rest_framework_oauth.authentication import OAuth2Authentication

from shoutit.controllers import mixpanel_controller
from shoutit.models import Page
from shoutit.utils import error_logger
from shoutit_credit.models.profile import apply_invite_friends


def get_authorization_header(request):
    """
    Return request's 'Authorization:' header, as a bytestring.

    Hide some test client ickyness where the header can be unicode.
    """
    auth = request.META.get('HTTP_AUTHORIZATION_PAGE_ID', b'')
    if isinstance(auth, type('')):
        # Work around django test client oddness
        auth = auth.encode(HTTP_HEADER_ENCODING)
    return auth


class ShoutitPageAuthenticationMixin(BaseAuthentication):
    """
    Shoutit Page based authentication.

    Clients should first authenticate using regular authentication. This mixin will switch request.user to the Page user
    if page id was passed in headers. The previous authenticated user should be one of the pages admins.

    Clients should authenticate by passing the page id in the "Authorization-Page-Id" HTTP header, For example:
        Authorization-Page-Id: 401f7ac837da42b97f613d789819ff93537bee6a
    """

    def authenticate(self, request):
        ret = super(ShoutitPageAuthenticationMixin, self).authenticate(request)
        if ret is None:
            return ret
        self.set_api_client(request, ret[1])

        page_id_auth = get_authorization_header(request).split()
        if not page_id_auth:
            return ret

        if len(page_id_auth) != 1:
            msg = _('Invalid page id header. No credentials provided')
            raise exceptions.AuthenticationFailed(msg)

        try:
            page_id = page_id_auth[0].decode()
            uuid.UUID(page_id)
        except (UnicodeError, ValueError):
            raise exceptions.AuthenticationFailed(_('Invalid page id'))

        try:
            page = Page.objects.select_related('user').get(id=page_id)
        except Page.DoesNotExist:
            raise exceptions.AuthenticationFailed(_('Page does not exist'))

        if not page.user.is_active:
            raise exceptions.AuthenticationFailed(_('Page inactive or deleted'))

        if not page.is_admin(ret[0]):
            raise exceptions.PermissionDenied(_("You can't act as an admin of the provided page"))

        setattr(request, '_user', page.user)
        setattr(request, 'page_admin_user', ret[0])
        return page.user, ret[1]

    def set_api_client(self, request, auth):
        """
        Set api_client to be used
        """
        if hasattr(auth, 'client'):
            # Authorized (AccessToken) DRF requests
            api_client = auth.client.name
            request.api_client = api_client

            # Todo: when no authorized it could be that this is from `shoutit-web`. A header must be agreed on to identify webapp requests even for guests. This should be done in a middleware outside auth.
            # elif 'node-superagent' in request.META.get('USER_AGENT', ''):
            #     request.api_client = 'shoutit-web'


class ShoutitTokenAuthentication(ShoutitPageAuthenticationMixin, TokenAuthentication):
    pass


class ShoutitOAuth2Authentication(ShoutitPageAuthenticationMixin, OAuth2Authentication):
    pass


class ShoutitSessionAuthentication(ShoutitPageAuthenticationMixin, SessionAuthentication):
    pass


class PostAccessTokenRequestMixin(object):
    def post_access_token_request(self):
        request = self.request
        data = request.data
        user = request.user
        new_signup = getattr(user, 'new_signup', False)

        mixpanel_distinct_id = data.get('mixpanel_distinct_id')
        invitation_code = data.get('invitation_code')
        track_properties = {
            'profile': user.pk,
            'api_client': data.get('client_id'),
            'api_version': request.version,
            'using': data.get('grant_type'),
            'server': request.META.get('HTTP_HOST'),
            'mp_country_code': user.location.get('country'),
            '$region': user.location.get('state'),
            '$city': user.location.get('city'),
            'has_push_tokens': user.devices.count() > 0,
            'invitation_code': invitation_code
        }

        if new_signup:
            event_name = "signup_guest" if user.is_guest else 'signup'
            # Apply InviteFriends
            if invitation_code:
                apply_invite_friends(request.user, invitation_code)
        else:
            event_name = 'login'

        if mixpanel_distinct_id:
            # Alias the Mixpanel id and track
            mixpanel_controller.alias(user.pk, mixpanel_distinct_id, event_name, track_properties, add=True)
        else:
            # Track only
            mixpanel_controller.track(user.pk, event_name, track_properties, add=True)
            # Y U NO send us Mixpanel?
            if data.get('grant_type') != 'refresh_token':
                extra = {'request': request._request, 'agent': request.agent, 'build_no': request.build_no,
                         'track_properties': track_properties, 'request_data': data}
                error_logger.warning('AccessToken request without mixpanel_distinct_id', extra=extra)
