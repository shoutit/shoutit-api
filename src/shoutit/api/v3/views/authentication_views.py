# -*- coding: utf-8 -*-
"""

"""
from __future__ import unicode_literals

from django.core.exceptions import ObjectDoesNotExist
from django.utils.translation import ugettext_lazy as _
from provider import constants as provider_constants, scope as provider_scope
from provider.oauth2.forms import ClientAuthForm
from provider.oauth2.models import AccessToken, RefreshToken, Client
from provider.oauth2.views import AccessTokenView as OAuthAccessTokenView
from provider.utils import now
from rest_framework import viewsets
from rest_framework.decorators import list_route
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.response import Response
from rest_framework.status import HTTP_401_UNAUTHORIZED
from rest_framework.views import APIView

from common.constants import TOKEN_TYPE_EMAIL
from shoutit.api.authentication import PostAccessTokenRequestMixin
from shoutit.api.v3.exceptions import ShoutitBadRequest, RequiredBody, InvalidBody, RequiredParameter, InvalidParameter
from shoutit.models import ConfirmToken
from ..serializers import (
    ShoutitSignupSerializer, ShoutitChangePasswordSerializer, ShoutitVerifyEmailSerializer, ShoutitPageSerializer,
    ShoutitSetPasswordSerializer, ShoutitResetPasswordSerializer, ShoutitLoginSerializer, ProfileDetailSerializer,
    FacebookAuthSerializer, GplusAuthSerializer, SMSCodeSerializer, ShoutitGuestSerializer, GuestSerializer,
    PageDetailSerializer)

INACTIVE_OR_DELETED = AuthenticationFailed(_('Account inactive or deleted'))


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


class AccessTokenView(PostAccessTokenRequestMixin, OAuthAccessTokenView, APIView):
    """
    OAuth2 Resource
    """
    # Client authentication
    authentication = (RequestParamsClientBackend,)
    # DRF authentication is not needed here
    authentication_classes = ()
    permission_classes = ()
    grant_types = ['authorization_code', 'refresh_token', 'client_credentials', 'facebook_access_token', 'gplus_code',
                   'shoutit_signup', 'shoutit_login', 'sms_code', 'shoutit_guest', 'shoutit_page']

    def access_token_response(self, access_token, data=None):
        """
        Returns a successful response after creating the access token
        as defined in :rfc:`5.1`.
        """
        if self.action == 'shoutit_page':
            user = self.page
        else:
            user = access_token.user
        if not user.is_active:
            raise INACTIVE_OR_DELETED

        # set the request user in case it is not set [refresh_token, password, etc grants]
        self.request.user = user

        if user.is_guest:
            user_dict = GuestSerializer(user, context={'request': self.request}).data
        elif hasattr(user, 'page'):
            user_dict = PageDetailSerializer(user, context={'request': self.request}).data
        else:
            user_dict = ProfileDetailSerializer(user, context={'request': self.request}).data

        response_data = {
            'access_token': access_token.token,
            'token_type': provider_constants.TOKEN_TYPE,
            'expires_in': access_token.get_expire_delta(),
            'scope': ' '.join(provider_scope.names(access_token.scope)),
            'profile': user_dict,
            'new_signup': getattr(user, 'new_signup', False)
        }

        # Todo (mo): deprecate as it is used by old clients only
        if self.action != 'shoutit_page':
            response_data['user'] = user_dict

        # Not all access_tokens are given a refresh_token
        # (for example, public clients doing password auth)
        try:
            rt = access_token.refresh_token
            response_data['refresh_token'] = rt.token
        except ObjectDoesNotExist:
            pass

        # Alias, Track, Apply InviteFriends, etc
        self.post_access_token_request()

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
        scopes = ('read', 'write')
        return self.prepare_access_token_response(request, client, user, scopes, data)

    def get_gplus_code_grant(self, request, data, client):
        serializer = GplusAuthSerializer(data=data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        return serializer.instance

    def gplus_code(self, request, data, client):
        """
        Handle ``grant_type=gplus_code`` requests.
        """
        user = self.get_gplus_code_grant(request, data, client)
        scopes = ('read', 'write')
        return self.prepare_access_token_response(request, client, user, scopes, data)

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
        scopes = ('read', 'write')
        return self.prepare_access_token_response(request, client, user, scopes, data)

    def get_shoutit_login_grant(self, request, login_data, client):
        serializer = ShoutitLoginSerializer(data=login_data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        return serializer.instance

    def shoutit_login(self, request, data, client):
        """
        Handle ``grant_type=shoutit_login`` requests.
        """
        user = self.get_shoutit_login_grant(request, data, client)
        scopes = ('read', 'write')
        return self.prepare_access_token_response(request, client, user, scopes, data)

    def get_shoutit_page_grant(self, request, login_data, client):
        serializer = ShoutitPageSerializer(data=login_data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        user, page = serializer.save()
        return user, page

    def shoutit_page(self, request, data, client):
        """
        Handle ``grant_type=shoutit_page`` requests.
        """
        user, page = self.get_shoutit_page_grant(request, data, client)
        self.page = page
        scopes = ('read', 'write')
        return self.prepare_access_token_response(request, client, user, scopes, data)

    def get_shoutit_guest_grant(self, request, guest_data, client):
        serializer = ShoutitGuestSerializer(data=guest_data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        return serializer.instance

    def shoutit_guest(self, request, data, client):
        """
        Handle ``grant_type=shoutit_guest`` requests.
        """
        user = self.get_shoutit_guest_grant(request, data, client)
        scopes = ('read',)
        return self.prepare_access_token_response(request, client, user, scopes, data)

    def get_sms_code_grant(self, request, data, client):
        serializer = SMSCodeSerializer(data=data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        return serializer.instance

    def sms_code(self, request, data, client):
        """
        Handle ``grant_type=sms_code`` requests.
        """
        user = self.get_sms_code_grant(request, data, client)
        scopes = ('read', 'write')
        return self.prepare_access_token_response(request, client, user, scopes, data)

    def prepare_access_token_response(self, request, client, user, scopes, data=None):
        self.request.user = user
        scope = provider_scope.to_int(*scopes)

        if provider_constants.SINGLE_ACCESS_TOKEN:
            at = self.get_access_token(request, user, scope, client)
        else:
            at = self.create_access_token(request, user, scope, client)
            # Public clients don't get refresh tokens
            if client.client_type == provider_constants.CONFIDENTIAL:
                self.create_refresh_token(request, user, scope, at, client)

        return self.access_token_response(at, data)

    def get_access_token(self, request, user, scope, client, refreshable=True):
        try:
            # Attempt to fetch an existing access token.
            access_tokens = AccessToken.objects.filter(user=user, client=client, scope=scope,
                                                       expires__gt=now()).order_by('-expires')
            # Single valid token. Return it
            if access_tokens.count() == 1:
                at = access_tokens[0]
            # No valid tokens. Raise exception to create one
            elif not access_tokens:
                raise AccessToken.DoesNotExist()
            # Multiple valid tokens. Take the first, which expires last, and delete the others
            else:
                at = access_tokens.first()
                access_tokens.exclude(id=at.id).delete()
        except AccessToken.DoesNotExist:
            # None found... make a new one!
            at = self.create_access_token(request, user, scope, client)
            if refreshable:
                self.create_refresh_token(request, user, scope, at, client)
        return at

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
        elif grant_type == 'shoutit_login':
            return self.shoutit_login
        elif grant_type == 'shoutit_page':
            return self.shoutit_page
        elif grant_type == 'shoutit_guest':
            return self.shoutit_guest
        elif grant_type == 'sms_code':
            return self.sms_code
        return None

    # override get, not to be documented or listed in urls.
    get = property()

    def post(self, request):
        """
        Authorize the profile and return an access token to be used in later API calls.

        The `profile` attribute in all signup / login calls is optional. It may have `location` dict with latitude and longitude.
        If valid location is passed, the profile will have it set, otherwise it will have an estimated location based on IP.

        When signing up and if there was a guest account saved, pass its `id` under the `profile` attribute. This will make sure the guest account is no longer guest. The Api will convert it to a normal account.

        Passing the optional `mixpanel_distinct_id` will allow API server to alias it with the actual profile id for later tracking events.

        Passing the optional `invitation_code` 'may' give the owner of that code a shoutit credit.

        ##Page Signup notes
        - returned `access_token` and `refresh_token` belong to the page creator (user)
        - returned `profile` is a DetailedPage and it contains `admin` which is a DetailedProfile for the page creator
        - clients should set http header `Authorization-Page-Id` using the returned `profile.id` for all later requests. This makes sure these calls are treated as if the Page is acting not its owner.

        ##Requesting the access token
        There are various methods to do that. Each has different `grant_type` and attributes.

        ###Using Google Code
        <pre><code>
        {
            "client_id": "shoutit-test",
            "client_secret": "d89339adda874f02810efddd7427ebd6",
            "grant_type": "gplus_code",
            "gplus_code": "4/04RAZxe3u9sp82yaUpzxmO_9yeYLibBcE5p0wq1szcQ.Yro5Y6YQChkeYFZr95uygvW7xDcmlwI",
            "profile": {
                "location": {
                    "latitude": 48.7533744,
                    "longitude": 11.3796516
                }
            },
            "mixpanel_distinct_id": "67da5c7b-8312-4dc5-b7c2-f09b30aa7fa1",
            "invitation_code": "V61DUM6K5W"
        }
        </code></pre>

        ###Using Facebook Access Token
        <pre><code>
        {
            "client_id": "shoutit-test",
            "client_secret": "d89339adda874f02810efddd7427ebd6",
            "grant_type": "facebook_access_token",
            "facebook_access_token": "CAAFBnuzd8h0BAA4dvVnscTb1qf9ye6ZCpq4NZCG7HJYIMHtQ0dfbZA95MbSZBzQSjFsvFwVzWr0NBibHxF5OuiXhEDMy",
            "profile": {
                "location": {
                    "latitude": 48.7533744,
                    "longitude": 11.3796516
                }
            },
            "mixpanel_distinct_id": "67da5c7b-8312-4dc5-b7c2-f09b30aa7fa1",
            "invitation_code": "V61DUM6K5W"
        }
        </code></pre>

        ###Using Shoutit Account
        <pre><code>
        {
            "client_id": "shoutit-test",
            "client_secret": "d89339adda874f02810efddd7427ebd6",
            "grant_type": "shoutit_login",
            "email": "i.also.shout@whitehouse.gov",
            "password": "iW@ntToPl*YaGam3",
            "profile": {
                "location": {
                    "latitude": 48.7533744,
                    "longitude": 11.3796516
                }
            },
            "mixpanel_distinct_id": "67da5c7b-8312-4dc5-b7c2-f09b30aa7fa1",
            "invitation_code": "V61DUM6K5W"
        }
        </code></pre>

        `email` can be email or username

        ###Creating Shoutit Account
        <pre><code>
        {
            "client_id": "shoutit-test",
            "client_secret": "d89339adda874f02810efddd7427ebd6",
            "grant_type": "shoutit_signup",
            "name": "Barack Hussein Obama",
            "email": "i.also.shout@whitehouse.gov",
            "password": "iW@ntToPl*YaGam3",
            "profile": {
                "location": {
                    "latitude": 48.7533744,
                    "longitude": 11.3796516
                }
            },
            "mixpanel_distinct_id": "67da5c7b-8312-4dc5-b7c2-f09b30aa7fa1",
            "invitation_code": "V61DUM6K5W"
        }
        </code></pre>

        ###Creating Shoutit Page
        <pre><code>
        {
            "client_id": "shoutit-test",
            "client_secret": "d89339adda874f02810efddd7427ebd6",
            "grant_type": "shoutit_page",
            "page_category": {
                "slug": "page-slug"
            },
            "page_name": "The White House",
            "name": "Barack Hussein Obama",
            "email": "i.also.shout@whitehouse.gov",
            "password": "iW@ntToPl*YaGam3",
            "profile": {
                "location": {
                    "latitude": 48.7533744,
                    "longitude": 11.3796516
                }
            },
            "mixpanel_distinct_id": "67da5c7b-8312-4dc5-b7c2-f09b30aa7fa1",
            "invitation_code": "V61DUM6K5W"
        }
        </code></pre>

        ###Creating Guest Account
        <pre><code>
        {
            "client_id": "shoutit-test",
            "client_secret": "d89339adda874f02810efddd7427ebd6",
            "grant_type": "shoutit_guest",
            "profile": {
                "location": {
                    "latitude": 48.7533744,
                    "longitude": 11.3796516
                },
                "push_tokens": {
                    "apns": "APNS_PUSH_TOKEN",
                    "gcm": "GCM_PUSH_TOKEN"
                },
            },
            "mixpanel_distinct_id": "67da5c7b-8312-4dc5-b7c2-f09b30aa7fa1",
            "invitation_code": "V61DUM6K5W"
        }
        </code></pre>

        ###Using SMS Code
        <pre><code>
        {
            "client_id": "shoutit-test",
            "client_secret": "d89339adda874f02810efddd7427ebd6",
            "grant_type": "sms_code",
            "sms_code": "07c59e",
        }
        </code></pre>

        ##Refreshing the Token
        <pre><code>
        {
            "client_id": "shoutit-test",
            "client_secret": "d89339adda874f02810efddd7427ebd6",
            "grant_type": "refresh_token",
            "refresh_token": "f2994c7507d5649c49ea50065e52a944b2324697"
        }
        </code></pre>

        ##Response
        <pre><code>
        {
            "access_token": "1bd93abdbe4e5b4949e17dce114d94d96f21fe4a",
            "token_type": "Bearer",
            "expires_in": 31480817,
            "refresh_token": "f2994c7507d5649c49ea50065e52a944b2324697",
            "scope": "read write read+write",
            "profile": {DetailedProfile, DetailedPage or Guest object},
            "new_signup": true
        }
        </code></pre>

        If the profile newly signed up `new_signup` will be set to true otherwise false.

        ###Guest object
        <pre><code>
         {
            "id": "349b2dfb-899d-4c00-9514-689e6f2cdeae",
            "type": "user",
            "api_url": "https://api.shoutit.com/v3/users/14969084019",
            "username": "14969084019",
            "is_guest": true,
            "date_joined": 1456090930,
            "location": {
                "latitude": 25.1993957,
                "longitude": 55.2738326,
                "country": "AE",
                "postal_code": "Dubai",
                "state": "Dubai",
                "city": "Dubai",
                "address": ""
            },
            "push_tokens": {
                "apns": "asdlfjorjrjrslfsfwrewrwejrlwejrwlrjwlrjwelrjwl",
                "gcm": null
            }
        }
        </code></pre>

        ##Using the Token in header for later API calls.
        ```
        Authorization: Bearer 1bd93abdbe4e5b4949e17dce114d94d96f21fe4a
        ```

        ---
        omit_serializer: true
        parameters:
            - name: body
              paramType: body
        """
        # Set `action` to be used when handling exceptions
        self.action = 'post'
        auth_failed = _("Authentication failed")

        if 'grant_type' not in request.data:
            raise RequiredBody('grant_type', message=auth_failed)

        grant_type = request.data.get('grant_type')
        if grant_type not in self.grant_types:
            raise InvalidBody('grant_type', message=_("Unsupported grant_type"))

        client = self.authenticate(request)
        if client is None:
            raise InvalidBody('client', message=auth_failed, developer_message="Invalid client")
        request.client = client
        request.is_test = client.name == 'shoutit-test'

        handler = self.get_handler(grant_type)
        data = request.data.copy()
        # Update the `action` and set it as the `grant_type` before calling the handler
        self.action = grant_type
        return handler(request, data, client)


class ShoutitAuthViewSet(viewsets.ViewSet):
    """
    ShoutitAuth Resource
    """

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
        user = access_token.user
        if not user.is_active:
            raise INACTIVE_OR_DELETED

        # set the request user in case it is not set
        self.request.user = user
        user_dict = ProfileDetailSerializer(user, context={'request': self.request}).data
        response_data = {
            'access_token': access_token.token,
            'token_type': provider_constants.TOKEN_TYPE,
            'expires_in': access_token.get_expire_delta(),
            'scope': ' '.join(provider_scope.names(access_token.scope)),
            'user': user_dict,
            'profile': user_dict,
        }

        # Not all access_tokens are given a refresh_token
        # (for example, public clients doing password auth)
        try:
            rt = access_token.refresh_token
            response_data['refresh_token'] = rt.token
        except ObjectDoesNotExist:
            pass

        return Response(response_data)

    @list_route(methods=['post'], suffix='Change Password')
    def change_password(self, request):
        """
        Change the current profile's password.
        ###REQUIRES AUTH
        ###Change password
        ####Body
        <pre><code>
        {
            "old_password": "easypass",
            "new_password": "HarD3r0n#",
            "new_password2": "HarD3r0n#"
        }
        </code></pre>

        `old_password` is only required if set before. check profile's `is_set_password` property
        ---
        omit_serializer: true
        parameters:
            - name: body
              paramType: body
        """
        serializer = ShoutitChangePasswordSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        return self.success_response("Password changed")

    @list_route(methods=['post'], permission_classes=(), suffix='Reset Password')
    def reset_password(self, request):
        """
        Send the profile a password-reset email.
        Used when profile forgot his password. `email` can be email or username.
        ###Reset password
        ####Body
        <pre><code>
        {
            "email": "email@example.com"
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
        return self.success_response(_("Password reset email will be sent soon"))

    @list_route(methods=['post'], permission_classes=(), suffix='Set Password')
    def set_password(self, request):
        """
        Set the password using a reset token. This changes the profiles's current password. `reset_token` is to be extracted from the url sent to profile's email.
        ###Set Password
        ####Body
        <pre><code>
        {
            "reset_token": "23456789876543245678987654",
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
        return self.success_response(_("New password set"))

    @list_route(methods=['get', 'post'], permission_classes=(), suffix='Verify Email')
    def verify_email(self, request):
        """
        Verify email and resend email verification.

        ###REQUIRES AUTH
        ###Resend email verification
        Body:
        `email` is optional to change the current email before sending the new verification
        <pre><code>
        {
            "email": "email@example.com"
        }
        </code></pre>

        ###Verify email
        Params:
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
            "success": "Verification email will be soon sent to xxx@mail.com"
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
            "profile": {Detailed Profile Object}
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
        # Todo: Utilize serializers
        if request.method == 'GET':
            token = request.query_params.get('token')
            if not token:
                raise RequiredParameter('token')
            try:
                cf = ConfirmToken.objects.get(type=TOKEN_TYPE_EMAIL, token=token)
                if cf.is_disabled:
                    raise ValueError()
                user = cf.user
                if not user.is_active:
                    raise INACTIVE_OR_DELETED
                user.activate()
                cf.is_disabled = True
                cf.save(update_fields=['is_disabled'])

                # Try to get a valid access token
                try:
                    access_token = self.get_access_token(user)
                    return self.access_token_response(access_token)
                # Todo (mo): when this case happens?
                except Exception:
                    return self.success_response(_("New password set"))
            except ConfirmToken.DoesNotExist:
                raise InvalidParameter('token', _("Token does not exist"))
            except ValueError:
                raise ShoutitBadRequest(_("Email address is already verified"))

        elif request.method == 'POST':
            if request.user.is_anonymous():
                return Response({"detail": _("Authentication credentials were not provided")},
                                status=HTTP_401_UNAUTHORIZED)
            if request.user.is_activated:
                return self.success_response(
                    _("Your email '%(email)s' is already verified") % {'email': request.user.email})
            serializer = ShoutitVerifyEmailSerializer(data=request.data, context={'request': request})
            serializer.is_valid(raise_exception=True)
            return self.success_response(
                "Verification email will be soon sent to %(email)s" % {'email': request.user.email})
        else:
            return Response()

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
