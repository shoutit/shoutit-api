# -*- coding: utf-8 -*-
"""

"""
from __future__ import unicode_literals

from django.core.exceptions import ObjectDoesNotExist

from provider import constants as provider_constants, scope as provider_scope
from provider.oauth2.forms import ClientAuthForm
from provider.oauth2.views import AccessTokenView as OAuthAccessTokenView
from provider.views import OAuthError

from rest_framework.response import Response
from rest_framework.views import APIView

from shoutit.controllers.facebook_controller import user_from_facebook_auth_response
from shoutit.controllers.gplus_controller import user_from_gplus_code


class RequestParamsClientBackend(object):
    """
    Backend that tries to authenticate a client through request parameters
    which might be in the request body or URI as defined in :rfc:`2.3.1`.
    Modified to work with DRF request.data instead request.REQUEST
    """
    def authenticate(self, request=None):
        if request is None:
            return None

        form = ClientAuthForm(request.data)

        if form.is_valid():
            return form.cleaned_data.get('client')

        return None


class AccessTokenView(OAuthAccessTokenView, APIView):

    # client authentication
    authentication = (
        RequestParamsClientBackend,
    )
    # DRF authentication is not needed here
    authentication_classes = ()
    permission_classes = ()

    grant_types = ['authorization_code', 'refresh_token', 'password', 'client_credentials', 'facebook_access_token', 'gplus_code']

    def error_response(self, error, content_type='application/json', status=400, **kwargs):
        """
        Return an error response to the client with default status code of
        *400* stating the error as outlined in :rfc:`5.2`.
        """
        return Response(error, status=400)

    def access_token_response(self, access_token, data=None):
        """
        Returns a successful response after creating the access token
        as defined in :rfc:`5.1`.
        """

        response_data = {
            'access_token': access_token.token,
            'token_type': provider_constants.TOKEN_TYPE,
            'expires_in': access_token.get_expire_delta(),
            'scope': ' '.join(provider_scope.names(access_token.scope)),
        }

        # Not all access_tokens are given a refresh_token
        # (for example, public clients doing password auth)
        try:
            rt = access_token.refresh_token
            response_data['refresh_token'] = rt.token
        except ObjectDoesNotExist:
            pass

        return Response(response_data)

    def get_facebook_access_token_grant(self, request, data, client):

        facebook_access_token = data['facebook_access_token']
        initial_user = 'user' in data and data['user'] or None

        error, user = user_from_facebook_auth_response(request, facebook_access_token, initial_user)
        if error:
            raise OAuthError({'error': str(error)})
        return user

    def facebook_access_token(self, request, data, client):
        """
        Handle ``grant_type=facebook_access_token`` requests.
        {
            "client_id": "shoutit-web",
            "client_secret": "a5499bf97ab54b671e34127bc43226ab78cf7e14",
            "grant_type": "facebook_access_token",
            "facebook_access_token": "CAAFBnuzd8h0BAA4dvVnscTb1qf9ye6ZCpq4NZCG7HJYIMHtQ0dfbZA95MbSZBzQSjFsvFwVzWr0NBibHxF5OuiXhEDMyUEBpc9pSKiFhrxmiVHE2kwbFWj8iBHEaGEkSgNXOcQaYuZCUlfJqunkDGPQ2rM5e7j5anYynp1nOEZBXB6g91wyn8JJoLXoPTOb3dzVKFn51rIboQHZCp2p6TUCSQvFhSJpGrcZD"
        }
        """

        user = self.get_facebook_access_token_grant(request, data, client)
        scope = provider_scope.to_int('read', 'write')

        if provider_constants.SINGLE_ACCESS_TOKEN:
            at = self.get_access_token(request, user, scope, client)
        else:
            at = self.create_access_token(request, user, scope, client)
            # Public clients don't get refresh tokens
            if client.client_type == provider_constants.CONFIDENTIAL:
                rt = self.create_refresh_token(request, user, scope, at, client)

        return self.access_token_response(at)

    def get_gplus_code_grant(self, request, data, client):

        gplus_code = data['gplus_code']
        initial_user = 'user' in data and data['user'] or None

        error, user = user_from_gplus_code(request, gplus_code, initial_user, client.name)
        if error:
            raise OAuthError({'error': str(error)})
        return user

    def gplus_code(self, request, data, client):
        """
        Handle ``grant_type=gplus_code`` requests.
        {
            "client_id": "shoutit-web",
            "client_secret": "a5499bf97ab54b671e34127bc43226ab78cf7e14",
            "grant_type": "gplus_code",
            "gplus_code": "4/04RAZxe3u9sp82yaUpzxmO_9yeYLibBcE5p0wq1szcQ.Yro5Y6YQChkeYFZr95uygvW7xDcmlwI"
        }
        """

        user = self.get_gplus_code_grant(request, data, client)
        scope = provider_scope.to_int('read', 'write')

        if provider_constants.SINGLE_ACCESS_TOKEN:
            at = self.get_access_token(request, user, scope, client)
        else:
            at = self.create_access_token(request, user, scope, client)
            # Public clients don't get refresh tokens
            if client.client_type == provider_constants.CONFIDENTIAL:
                rt = self.create_refresh_token(request, user, scope, at, client)

        return self.access_token_response(at)

    def get_handler(self, grant_type):
        """
        Return a function or method that is capable handling the ``grant_type``
        requested by the client or return ``None`` to indicate that this type
        of grant type is not supported, resulting in an error response.
        """
        if grant_type == 'authorization_code':
            return self.authorization_code
        elif grant_type == 'refresh_token':
            return self.refresh_token
        elif grant_type == 'password':
            return self.password
        elif grant_type == 'client_credentials':
            return self.client_credentials
        elif grant_type == 'facebook_access_token':
            return self.facebook_access_token
        elif grant_type == 'gplus_code':
            return self.gplus_code
        return None

    def post(self, request):
        """
        As per :rfc:`3.2` the token endpoint *only* supports POST requests.
        Modified to work with DRF request.data instead request.REQUEST
        """
        if provider_constants.ENFORCE_SECURE and not request.is_secure():
            return self.error_response({
                'error': 'invalid_request',
                'error_description': "A secure connection is required."})

        if 'grant_type' not in request.data:
            return self.error_response({
                'error': 'invalid_request',
                'error_description': "No 'grant_type' included in the request."
            })

        grant_type = request.data['grant_type']

        if grant_type not in self.grant_types:
            return self.error_response({'error': 'unsupported_grant_type'})

        client = self.authenticate(request)

        if client is None:
            return self.error_response({'error': 'invalid_client'})

        handler = self.get_handler(grant_type)

        try:
            return handler(request, request.data, client)
        except OAuthError, e:
            return self.error_response(e.args[0])