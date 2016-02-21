"""

"""
from __future__ import unicode_literals

import uuid

from rest_framework import HTTP_HEADER_ENCODING, exceptions
from rest_framework.authentication import BaseAuthentication, TokenAuthentication, SessionAuthentication
from rest_framework_oauth.authentication import OAuth2Authentication

from shoutit.models import Page


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

        page_id_auth = get_authorization_header(request).split()
        if not page_id_auth:
            return ret

        if len(page_id_auth) != 1:
            msg = 'Invalid page id header. No credentials provided.'
            raise exceptions.AuthenticationFailed(msg)

        try:
            page_id = page_id_auth[0].decode()
            uuid.UUID(page_id)
        except (UnicodeError, ValueError):
            raise exceptions.AuthenticationFailed('Invalid page id.')

        try:
            page = Page.objects.select_related('user').get(id=page_id)
        except Page.DoesNotExist:
            raise exceptions.AuthenticationFailed('Page does not exist.')

        if not page.user.is_active:
            raise exceptions.AuthenticationFailed('Page inactive or deleted.')

        setattr(request, '_user', page.user)
        setattr(request, 'page_admin_user', ret[0])
        return page.user, ret[1]


class ShoutitTokenAuthentication(ShoutitPageAuthenticationMixin, TokenAuthentication):
    pass


class ShoutitOAuth2Authentication(ShoutitPageAuthenticationMixin, OAuth2Authentication):
    pass


class ShoutitSessionAuthentication(ShoutitPageAuthenticationMixin, SessionAuthentication):
    pass