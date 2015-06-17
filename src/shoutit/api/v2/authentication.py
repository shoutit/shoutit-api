# -*- coding: utf-8 -*-
"""

"""
from __future__ import unicode_literals

from django.core.exceptions import ObjectDoesNotExist
from ipware.ip import get_ip

from provider import constants as provider_constants, scope as provider_scope
from provider.oauth2.forms import ClientAuthForm
from provider.oauth2.views import AccessTokenView as OAuthAccessTokenView
from provider.views import OAuthError

from rest_framework import viewsets, status
from rest_framework.decorators import list_route
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.exceptions import ValidationError
from common.constants import TOKEN_TYPE_EMAIL, COUNTRY_ISO
from shoutit.api.v2.serializers import (
    ShoutitSignupSerializer, ShoutitChangePasswordSerializer, ShoutitVerifyEmailSerializer,
    ShoutitSetPasswordSerializer, ShoutitResetPasswordSerializer, ShoutitSigninSerializer,
    UserDetailSerializer)
from shoutit.controllers.facebook_controller import user_from_facebook_auth_response
from shoutit.controllers.gplus_controller import user_from_gplus_code
from shoutit.models import ConfirmToken
from shoutit.utils import track, alias


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


class AccessTokenView(APIView, OAuthAccessTokenView):
    """
    OAuth2 Resource
    """

    # client authentication
    authentication = (
        RequestParamsClientBackend,
    )
    # DRF authentication is not needed here
    authentication_classes = ()
    permission_classes = ()

    grant_types = ['authorization_code', 'refresh_token', 'client_credentials',
                   'facebook_access_token', 'gplus_code', 'shoutit_signup', 'shoutit_signin']

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

        # set the request user in case it is not set [refresh_token, password, etc grants]
        user = access_token.user
        self.request.user = user
        user_dict = UserDetailSerializer(user, context={'request': self.request}).data
        new_signup = getattr(user, 'new_signup', False)

        response_data = {
            'access_token': access_token.token,
            'token_type': provider_constants.TOKEN_TYPE,
            'expires_in': access_token.get_expire_delta(),
            'scope': ' '.join(provider_scope.names(access_token.scope)),
            'user': user_dict,
            'new_signup': new_signup
        }

        # Not all access_tokens are given a refresh_token
        # (for example, public clients doing password auth)
        try:
            rt = access_token.refresh_token
            response_data['refresh_token'] = rt.token
        except ObjectDoesNotExist:
            pass

        # alias the mixpanel id and track registration
        request_data = self.request.data
        if new_signup:
            # alias(request_data.get('mixpanel_distinct_id'), user.pk)
            track(user.pk, 'signup', {
                'api_client': request_data.get('client_id'),
                'using': request_data.get('grant_type'),
                'server': self.request.META.get('HTTP_HOST'),
                'Country': COUNTRY_ISO.get(user.location.get('country')),
                'Region': user.location.get('state'),
                'City': user.location.get('city'),
            })

        return Response(response_data)

    def get_facebook_access_token_grant(self, request, data, client):

        facebook_access_token = data.get('facebook_access_token')
        if not facebook_access_token:
            raise OAuthError({'invalid_request': "Missing required parameter: facebook_access_token"})
        initial_user = data.get('user', {})
        initial_user['ip'] = get_ip(request)

        user = user_from_facebook_auth_response(facebook_access_token, initial_user)
        return user

    def facebook_access_token(self, request, data, client):
        """
        Handle ``grant_type=facebook_access_token`` requests.
        {
            "client_id": "shoutit-test",
            "client_secret": "d89339adda874f02810efddd7427ebd6",
            "grant_type": "facebook_access_token",
            "facebook_access_token": "CAAFBnuzd8h0BAA4dvVnscTb1qf9ye6ZCpq4NZCG7HJYIMHtQ0dfbZA95MbSZBzQSjFsvFwVzWr0NBibHxF5OuiXhEDMy"
        }
        """

        user = self.get_facebook_access_token_grant(request, data, client)
        self.request.user = user
        scope = provider_scope.to_int('read', 'write')

        if provider_constants.SINGLE_ACCESS_TOKEN:
            at = self.get_access_token(request, user, scope, client)
        else:
            at = self.create_access_token(request, user, scope, client)
            # Public clients don't get refresh tokens
            if client.client_type == provider_constants.CONFIDENTIAL:
                self.create_refresh_token(request, user, scope, at, client)

        return self.access_token_response(at)

    def get_gplus_code_grant(self, request, data, client):

        gplus_code = data.get('gplus_code')
        if not gplus_code:
            raise OAuthError({'invalid_request': "Missing required parameter: gplus_code"})
        initial_user = data.get('user', {})
        initial_user['ip'] = get_ip(request)

        user = user_from_gplus_code(gplus_code, initial_user, client.name)
        return user

    def gplus_code(self, request, data, client):
        """
        Handle ``grant_type=gplus_code`` requests.
        {
            "client_id": "shoutit-test",
            "client_secret": "d89339adda874f02810efddd7427ebd6",
            "grant_type": "gplus_code",
            "gplus_code": "4/04RAZxe3u9sp82yaUpzxmO_9yeYLibBcE5p0wq1szcQ.Yro5Y6YQChkeYFZr95uygvW7xDcmlwI"
        }
        """

        user = self.get_gplus_code_grant(request, data, client)
        self.request.user = user
        scope = provider_scope.to_int('read', 'write')

        if provider_constants.SINGLE_ACCESS_TOKEN:
            at = self.get_access_token(request, user, scope, client)
        else:
            at = self.create_access_token(request, user, scope, client)
            # Public clients don't get refresh tokens
            if client.client_type == provider_constants.CONFIDENTIAL:
                self.create_refresh_token(request, user, scope, at, client)

        return self.access_token_response(at)

    def get_shoutit_signup_grant(self, request, signup_data, client):
        serializer = ShoutitSignupSerializer(data=signup_data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return user

    def shoutit_signup(self, request, data, client):
        """
        Handle ``grant_type=shoutit_signup`` requests.
        {
            "client_id": "shoutit-test",
            "client_secret": "d89339adda874f02810efddd7427ebd6",
            "grant_type": "shoutit_signup",
            "name": "Barack Hussein Obama",
            "email": "i.also.shout@whitehouse.gov",
            "password": "iW@ntToPl*YaGam3"
        }
        """

        user = self.get_shoutit_signup_grant(request, data, client)
        self.request.user = user
        scope = provider_scope.to_int('read', 'write')

        if provider_constants.SINGLE_ACCESS_TOKEN:
            at = self.get_access_token(request, user, scope, client)
        else:
            at = self.create_access_token(request, user, scope, client)
            # Public clients don't get refresh tokens
            if client.client_type == provider_constants.CONFIDENTIAL:
                self.create_refresh_token(request, user, scope, at, client)

        return self.access_token_response(at)

    def get_shoutit_signin_grant(self, request, signin_data, client):
        serializer = ShoutitSigninSerializer(data=signin_data)
        serializer.is_valid(raise_exception=True)
        return serializer.instance

    def shoutit_signin(self, request, data, client):
        """
        Handle ``grant_type=shoutit_signin`` requests.
        {
            "client_id": "shoutit-test",
            "client_secret": "d89339adda874f02810efddd7427ebd6",
            "grant_type": "shoutit_signin",
            "email": "i.also.shout@whitehouse.gov",  // email or username
            "password": "iW@ntToPl*YaGam3"
        }
        """

        user = self.get_shoutit_signin_grant(request, data, client)
        self.request.user = user
        scope = provider_scope.to_int('read', 'write')

        if provider_constants.SINGLE_ACCESS_TOKEN:
            at = self.get_access_token(request, user, scope, client)
        else:
            at = self.create_access_token(request, user, scope, client)
            # Public clients don't get refresh tokens
            if client.client_type == provider_constants.CONFIDENTIAL:
                self.create_refresh_token(request, user, scope, at, client)

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
        elif grant_type == 'shoutit_signup':
            return self.shoutit_signup
        elif grant_type == 'shoutit_signin':
            return self.shoutit_signin
        return None

    # override get, not to be documented or listed in urls.
    get = property()

    def post(self, request):
        """
        Authorize the user and return an access token to be used in later API calls.

        The `user` attribute in all signup calls is optional. It may have full location information, or the response from google geocode maps call.

        ###Using Google Code
        <pre><code>
        {
            "client_id": "shoutit-test",
            "client_secret": "d89339adda874f02810efddd7427ebd6",
            "grant_type": "gplus_code",
            "gplus_code": "4/04RAZxe3u9sp82yaUpzxmO_9yeYLibBcE5p0wq1szcQ.Yro5Y6YQChkeYFZr95uygvW7xDcmlwI",
            "user": {
                "location": {
                    "google_geocode_response": {}
                }
            },
            "mixpanel_distinct_id": "67da5c7b-8312-4dc5-b7c2-f09b30aa7fa1"
        }
        </code></pre>


        ###Using Facebook Access Token
        <pre><code>
        {
            "client_id": "shoutit-test",
            "client_secret": "d89339adda874f02810efddd7427ebd6",
            "grant_type": "facebook_access_token",
            "facebook_access_token": "CAAFBnuzd8h0BAA4dvVnscTb1qf9ye6ZCpq4NZCG7HJYIMHtQ0dfbZA95MbSZBzQSjFsvFwVzWr0NBibHxF5OuiXhEDMy",
            "user": {
                "location": {
                    "google_geocode_response": {}
                }
            },
            "mixpanel_distinct_id": "67da5c7b-8312-4dc5-b7c2-f09b30aa7fa1"
        }
        </code></pre>

        ###Creating Shoutit Account
        <pre><code>
        {
            "client_id": "shoutit-test",
            "client_secret": "d89339adda874f02810efddd7427ebd6",
            "grant_type": "shoutit_signup",
            "name": "Barack Hussein Obama",
            "email": "i.also.shout@whitehouse.gov",
            "password": "iW@ntToPl*YaGam3",
            "user": {
                "location": {
                    "google_geocode_response": {}
                }
            },
            "mixpanel_distinct_id": "67da5c7b-8312-4dc5-b7c2-f09b30aa7fa1"
        }
        </code></pre>

        ###Signin with Shoutit Account
        <pre><code>
        {
            "client_id": "shoutit-test",
            "client_secret": "d89339adda874f02810efddd7427ebd6",
            "grant_type": "shoutit_signin",
            "email": "i.also.shout@whitehouse.gov",  // email or username
            "password": "iW@ntToPl*YaGam3"
        }
        </code></pre>

        ###Refreshing the Token
        <pre><code>
        {
            "client_id": "shoutit-test",
            "client_secret": "d89339adda874f02810efddd7427ebd6",
            "grant_type": "refresh_token",
            "refresh_token": "f2994c7507d5649c49ea50065e52a944b2324697"
        }
        </code></pre>

        ###Response
        <pre><code>
        {
            "access_token": "1bd93abdbe4e5b4949e17dce114d94d96f21fe4a",
            "token_type": "Bearer",
            "expires_in": 31480817,
            "refresh_token": "f2994c7507d5649c49ea50065e52a944b2324697",
            "scope": "read write read+write"
            "user": {Detailed User Object}
            "new_signup": true
        }
        </code></pre>

        if the user newly signed up `new_signup` will be set to true otherwise false. If the location was initially passed Users objects will it, otherwise they will have an estimated location based on their IP.

        ###Using the Token in header for later API calls.
        ```
        Authorization: Bearer 1bd93abdbe4e5b4949e17dce114d94d96f21fe4a
        ```

        ---
        omit_serializer: true
        parameters:
            - name: body
              paramType: body
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

        grant_type = request.data.get('grant_type')

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


class ShoutitAuthViewSet(viewsets.ViewSet):
    """
    ShoutitAuth Resource
    """

    def error_response(self, error):
        """
        Return an error response to the client with default status code of
        *400* stating the error as outlined in :rfc:`5.2`.
        """
        response_data = {
            'error': error,
        }
        return Response(response_data, status=400)

    def success_response(self, success):
        """
        Returns a successful response.
        """
        response_data = {
            'success': success,
        }
        return Response(response_data)

    @list_route(methods=['get', 'post'], permission_classes=(), suffix='Verify Email')
    def verify_email(self, request):
        """
        ###Verify email
        GET:
        <pre><code>
        GET: /auth/verify_email?token=39097c224b0f4ffb8923fc92337ec90bd71d294092aa4bbaa2e8c91854fd891e
        </code></pre>

        ###Resend email verification
        POST:
        <pre><code>
        {
            "email": "email@example.com"  // optional to change the email before sending new verification email
        }
        </code></pre>

        ---
        omit_serializer: true
        parameters:
            - name: body
              paramType: body
            - name: token
              paramType: query
        """
        if request.method == 'GET':
            token = request.query_params.get('token')
            if not token:
                raise ValidationError({'token': "This parameter is required."})
            try:
                cf = ConfirmToken.objects.get(type=TOKEN_TYPE_EMAIL, token=token, is_disabled=False)
                user = cf.user
                user.activate()
                cf.is_disabled = True
                cf.save(update_fields=['is_disabled'])
                return self.success_response("Your email has been verified.")
            except ConfirmToken.DoesNotExist:
                return self.error_response("Token does not exist.")

        elif request.method == 'POST':
            if request.user.is_anonymous():
                return Response({"detail": "Authentication credentials were not provided."},
                                status=status.HTTP_401_UNAUTHORIZED)
            if request.user.is_activated:
                return self.success_response(
                    "Your email '{}' is already verified.".format(request.user.email))
            serializer = ShoutitVerifyEmailSerializer(data=request.data,
                                                      context={'request': request})
            serializer.is_valid(raise_exception=True)
            serializer.instance.send_verification_email()
            return self.success_response(
                "Verification email will be soon sent to {}.".format(request.user.email))
        else:
            return Response()

    @list_route(methods=['post'], suffix='Change Password')
    def change_password(self, request):
        """
        ###Change password
        This changes the current user's password.
        <pre><code>
        {
            "old_password": "easypass", // only required if set before. check user.is_set_password
            "new_password": "HarD3r0n#",
            "new_password2": "HarD3r0n#"
        }
        </code></pre>

        ---
        omit_serializer: true
        parameters:
            - name: body
              paramType: body
        """
        serializer = ShoutitChangePasswordSerializer(data=request.data,
                                                     context={'request': request})
        serializer.is_valid(raise_exception=True)
        return self.success_response("Password changed.")

    @list_route(methods=['post'], permission_classes=(), suffix='Reset Password')
    def reset_password(self, request):
        """
        ###Reset password
        This sends the user a password reset email. It can be used when user forgets his password.
        <pre><code>
        {
            "email": "email@example.com"  // email or username
        }
        </code></pre>

        ---
        omit_serializer: true
        parameters:
            - name: body
              paramType: body
        """
        serializer = ShoutitResetPasswordSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.instance.reset_password()
        return self.success_response("Password reset email will be sent soon.")

    @list_route(methods=['post'], permission_classes=(), suffix='Set Password')
    def set_password(self, request):
        """
        ###Set password using reset token
        This changes the current user's password.
        <pre><code>
        {
            "reset_token": "23456789876543245678987654", // the WebApp should extract this from url send to user's email
            "new_password": "HarD3r0n#",
            "new_password2": "HarD3r0n#"
        }
        </code></pre>

        ---
        omit_serializer: true
        parameters:
            - name: body
              paramType: body
        """
        serializer = ShoutitSetPasswordSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        return self.success_response("New password set.")
