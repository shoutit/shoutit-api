# -*- coding: utf-8 -*-
"""

"""
from __future__ import unicode_literals

from django.core.exceptions import ObjectDoesNotExist

from provider import constants as provider_constants, scope as provider_scope
from provider.oauth2.forms import ClientAuthForm
from provider.oauth2.views import AccessTokenView as OAuthAccessTokenView
from provider.utils import now
from provider.views import OAuthError
from provider.oauth2.models import AccessToken, RefreshToken, Client

from rest_framework import viewsets
from rest_framework.decorators import list_route
from rest_framework.response import Response
from rest_framework.status import HTTP_401_UNAUTHORIZED
from rest_framework.views import APIView
from rest_framework.exceptions import ValidationError
from common.constants import TOKEN_TYPE_EMAIL, COUNTRY_ISO
from shoutit.api.v2.serializers import (
    ShoutitSignupSerializer, ShoutitChangePasswordSerializer, ShoutitVerifyEmailSerializer,
    ShoutitSetPasswordSerializer, ShoutitResetPasswordSerializer, ShoutitSigninSerializer,
    UserDetailSerializer, FacebookAuthSerializer, GplusAuthSerializer, SMSCodeSerializer)
from shoutit.models import ConfirmToken
from shoutit.utils import track, alias, error_logger


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
                   'facebook_access_token', 'gplus_code', 'shoutit_signup', 'shoutit_signin',
                   'sms_code']

    def error_response(self, error, **kwargs):
        """
        Return an error response to the client with default status code of
        *400* stating the error as outlined in :rfc:`5.2`.
        """
        client = kwargs.get('client')
        client_name = client.name if client else 'NoClient'
        grant_type = kwargs.get('grant_type', 'NoGrant')
        error_name = "oAuth2 Error - %s - %s" % (client_name, grant_type)
        error_logger.warn(error_name, extra={'detail': error, 'request_data': self.request.data})
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
            mixpanel_distinct_id = request_data.get('mixpanel_distinct_id')
            if mixpanel_distinct_id:
                alias(user.pk, mixpanel_distinct_id)
            track(user.pk, 'signup', {
                'user_id': user.pk,
                'api_client': request_data.get('client_id'),
                'using': request_data.get('grant_type'),
                'server': self.request.META.get('HTTP_HOST'),
                'Country': COUNTRY_ISO.get(user.location.get('country')),
                'Region': user.location.get('state'),
                'City': user.location.get('city'),
            })

        return Response(response_data)

    def get_facebook_access_token_grant(self, request, data, client):
        serializer = FacebookAuthSerializer(data=data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        return serializer.instance

    def facebook_access_token(self, request, data, client):
        """
        Handle ``grant_type=facebook_access_token`` requests.
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
        data.update({'client_name': client.name})
        serializer = GplusAuthSerializer(data=data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        return serializer.instance

    def gplus_code(self, request, data, client):
        """
        Handle ``grant_type=gplus_code`` requests.
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
        signin_data.update({'client_name': client.name})
        serializer = ShoutitSigninSerializer(data=signin_data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        return serializer.instance

    def shoutit_signin(self, request, data, client):
        """
        Handle ``grant_type=shoutit_signin`` requests.
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

    def get_sms_code_grant(self, request, data, client):
        serializer = SMSCodeSerializer(data=data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        return serializer.instance

    def sms_code(self, request, data, client):
        """
        Handle ``grant_type=sms_code`` requests.
        """
        user = self.get_sms_code_grant(request, data, client)
        return self.prepare_access_token_response(request, client, user)

    def prepare_access_token_response(self, request, client, user):
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
        elif grant_type == 'sms_code':
            return self.sms_code
        return None

    # override get, not to be documented or listed in urls.
    get = property()

    def post(self, request):
        """
        Authorize the user and return an access token to be used in later API calls.

        The `user` attribute in all signup / signin calls is optional. It may have full location information, or better the JSON response from google geocode maps call.
        If valid location is passed, user's profile will have it set, otherwise it will have an estimated location based on IP.

        Passing the optional `mixpanel_distinct_id` will allow API server to alias it with the actual user id for later tracking events.

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

        ###Signin with SMS Code
        <pre><code>
        {
            "client_id": "shoutit-test",
            "client_secret": "d89339adda874f02810efddd7427ebd6",
            "grant_type": "sms_code",
            "sms_code": "07c59e",
        }
        </code></pre>

        `email` can be email or username

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
            "scope": "read write read+write",
            "user": {Detailed User Object},
            "new_signup": true
        }
        </code></pre>

        If the user newly signed up `new_signup` will be set to true otherwise false.

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
                'error_description': "A secure connection is required."
            })

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
            return self.error_response(e.args[0], client=client, grant_type=grant_type)
        except ValidationError as e:
            return self.error_response(e.detail, client=client, grant_type=grant_type)
        except Exception as e:
            return self.error_response(str(e), client=client, grant_type=grant_type)


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

    def access_token_response(self, access_token):
        """
        Returns a successful response after creating the access token
        as defined in :rfc:`5.1`.
        """

        # set the request user in case it is not set
        user = access_token.user
        self.request.user = user
        user_dict = UserDetailSerializer(user, context={'request': self.request}).data

        response_data = {
            'access_token': access_token.token,
            'token_type': provider_constants.TOKEN_TYPE,
            'expires_in': access_token.get_expire_delta(),
            'scope': ' '.join(provider_scope.names(access_token.scope)),
            'user': user_dict,
        }

        # Not all access_tokens are given a refresh_token
        # (for example, public clients doing password auth)
        try:
            rt = access_token.refresh_token
            response_data['refresh_token'] = rt.token
        except ObjectDoesNotExist:
            pass

        return Response(response_data)

    @list_route(methods=['get', 'post'], permission_classes=(), suffix='Verify Email')
    def verify_email(self, request):
        """
        This endpoint requires authentication headers!

        ##Resend email verification
        POST:
        <pre><code>
        {
            "email": "email@example.com"
        }
        </code></pre>
        `email` is optional to change the current email before sending the new verification

        ##Verify email
        GET:
        <pre><code>
        GET: /auth/verify_email?token=39097c224b0f4ffb8923fc92337ec90bd71d294092aa4bbaa2e8c91854fd891e
        </code></pre>


        ###Result
        API server will send an email to the user with webapp link such as:
        <pre><code>
        www.shoutit.com/services/verify_email&verify_token=xxx
        </code></pre>

        Webapp should get the token and send an "api" call to:
        <pre><code>
        GET: /auth/verify_email?token=xxx
        </code></pre>

        ###Response(s)
        ##POST
        <pre><code>
        {
            "success": "Your email 'xxx@mail.com' is already verified"
        }
        </code></pre>
        or
        <pre><code>
        {
            "success": "Verification email will be soon sent to xxx@mail.com."
        }
        </code></pre>


        ##GET
        The main response
        <pre><code>
        {
            "access_token": "1bd93abdbe4e5b4949e17dce114d94d96f21fe4a",
            "token_type": "Bearer",
            "expires_in": 31480817,
            "refresh_token": "f2994c7507d5649c49ea50065e52a944b2324697",
            "scope": "read write read+write",
            "user": {Detailed User Object}
        }
        </code></pre>

        In some cases the response will just look like:
        <pre><code>
        {
            "success": "Your email has been verified"
        }
        </code></pre>
        or
        <pre><code>
        {
            "error": "Email address is already verified"
        }
        </code></pre>
        or
        <pre><code>
        {
            "error": "Token does not exist"
        }
        </code></pre>
        In any of these cases, show the user the message and below it a link to log in page.

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
                cf = ConfirmToken.objects.get(type=TOKEN_TYPE_EMAIL, token=token)
                if cf.is_disabled:
                    raise ValueError()
                user = cf.user
                user.activate()
                cf.is_disabled = True
                cf.save(update_fields=['is_disabled'])

                # Try to get a valid access token
                try:
                    access_token = self.get_access_token(user)
                    return self.access_token_response(access_token)
                except Exception:
                    return self.success_response("Your email has been verified.")
            except ConfirmToken.DoesNotExist:
                return self.error_response("Token does not exist.")
            except ValueError:
                return self.error_response("Email address is already verified.")

        elif request.method == 'POST':
            if request.user.is_anonymous():
                return Response({"detail": "Authentication credentials were not provided."},
                                status=HTTP_401_UNAUTHORIZED)
            if request.user.is_activated:
                return self.success_response("Your email '{}' is already verified.".format(request.user.email))
            serializer = ShoutitVerifyEmailSerializer(data=request.data, context={'request': request})
            serializer.is_valid(raise_exception=True)
            return self.success_response("Verification email will be soon sent to {}.".format(request.user.email))
        else:
            return Response()

    @list_route(methods=['post'], suffix='Change Password')
    def change_password(self, request):
        """
        ###Change password
        This changes the current user's password.
        <pre><code>
        {
            "old_password": "easypass",
            "new_password": "HarD3r0n#",
            "new_password2": "HarD3r0n#"
        }
        </code></pre>

        `old_password` is only required if set before. check user's `is_set_password` property

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
        This sends the user a password reset email. Used when user forgot his password.
        <pre><code>
        {
            "email": "email@example.com"
        }
        </code></pre>

        `email` can be email or username

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
        This changes the user's current password.
        <pre><code>
        {
            "reset_token": "23456789876543245678987654",
            "new_password": "HarD3r0n#",
            "new_password2": "HarD3r0n#"
        }
        </code></pre>

        `reset_token` is to be extracted from the url sent to user's email

        ---
        omit_serializer: true
        parameters:
            - name: body
              paramType: body
        """
        serializer = ShoutitSetPasswordSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        return self.success_response("New password set.")

    # OAuth2 methods
    def get_access_token(self, user):
        client = Client.objects.get(name='shoutit-web')
        scope = provider_scope.to_int('read', 'write')
        try:
            # Attempt to fetch an existing access token.
            at = AccessToken.objects.get(user=user, client=client, scope=scope, expires__gt=now())
        except AccessToken.DoesNotExist:
            # None found... make a new one!
            at = self.create_access_token(user, scope, client)
            self.create_refresh_token(at)
        return at

    def create_access_token(self, user, scope, client):
        return AccessToken.objects.create(user=user, client=client, scope=scope)

    def create_refresh_token(self, at):
        return RefreshToken.objects.create(user=at.user, access_token=at, client=at.client)