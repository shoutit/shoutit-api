# -*- coding: utf-8 -*-
"""

"""
from __future__ import unicode_literals

import uuid
from collections import OrderedDict

from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.utils import timezone
from rest_framework import viewsets
from rest_framework.decorators import list_route
from rest_framework.response import Response
from twilio.access_token import AccessToken, ConversationsGrant

from shoutit.api.v3.exceptions import ShoutitBadRequest, RequiredParameter, InvalidParameter
from shoutit.api.v3.serializers import ProfileSerializer
from shoutit.models import User
from shoutit_twilio.models import VideoClient
from .settings import SHOUTIT_TWILIO_SETTINGS


class ShoutitTwilioViewSet(viewsets.ViewSet):
    """
    Shoutit Twilio API Resources.
    """

    @list_route(methods=['post'], suffix='Authorize Video Client')
    def video_auth(self, request):
        """
        Create a video chat endpoint.
        ###REQUIRES AUTH
        ###Response
        <pre><code>
        {
          "token": "eyJhbGciOiAiSFMyNTYiLCAidHlwIjogIkpXVCIsICJjdHkiOiAidHdpbGlvLWZwYTt2PTEifQ.eyJpc3MiOiAiU0s3MDFlYzE",
          "identity": "7c6ca4737db3447f936037374473e61f"
        }
        </code></pre>
        ---
        """
        user = request.user
        try:
            video_client = user.video_client

            # Check whether client has an expired token
            if timezone.now() > video_client.expires_at:
                video_client.delete()
                raise ValueError()
        except (AttributeError, ValueError):
            # Get credentials
            account_sid = SHOUTIT_TWILIO_SETTINGS['TWILIO_ACCOUNT_SID']
            api_key = SHOUTIT_TWILIO_SETTINGS['TWILIO_API_KEY']
            api_secret = SHOUTIT_TWILIO_SETTINGS['TWILIO_API_SECRET']

            # Create identity for the token using random uuid.hex (not to have the hyphens)
            identity = uuid.uuid4().hex

            # Create an Access Token
            token = AccessToken(account_sid, api_key, api_secret, identity=identity)

            # Grant access to Conversations
            grant = ConversationsGrant(configuration_profile_sid=SHOUTIT_TWILIO_SETTINGS['TWILIO_CONFIGURATION_SID'])
            token.add_grant(grant)

            # Create VideoClient
            jwt_token = token.to_jwt()
            try:
                video_client = VideoClient.create(id=identity, user=user, token=jwt_token)
            except (ValidationError, IntegrityError) as e:
                msg = "Couldn't authorize you to make video calls"
                raise ShoutitBadRequest(message=msg, developer_message=unicode(e))

        # Return token info
        res = OrderedDict([
            ('identity', video_client.identity),
            ('token', video_client.token),
            ('expires_at', video_client.expires_at_unix)
        ])
        return Response(res)

    @list_route(methods=['get'], suffix='Retrieve Identity')
    def video_identity(self, request):
        """
        Retrieve video client identity to make a call
        <pre><code>
        GET: /twilio/video_identity?profile=username
        </code></pre>

        ###REQUIRES AUTH

        ###Response
        <pre><code>
        {
          "identity": "7c6ca4737db3447f936037374473e61f"
        }
        </code></pre>

        Returns 403 if the call is not allowed.
        ---
        omit_serializer: true
        parameters:
            - name: profile
              description: Profile username
              paramType: query
        """
        # Todo: Check whether calling user is allowed to do this call or not

        other_username = request.query_params.get('profile')
        if not other_username:
            raise RequiredParameter('profile')

        try:
            other_user = User.objects.get(username=other_username)
        except User.DoesNotExist:
            msg = "Profile with username %s doesn't exist" % other_username
            raise InvalidParameter('profile', message=msg)

        if hasattr(other_user, 'video_client'):
            video_client = other_user.video_client
        else:
            msg = "Profile with username %s is not online" % other_username
            raise InvalidParameter('profile', message=msg)

        res = {
            'identity': video_client.identity
        }
        return Response(res)

    @list_route(methods=['get'], suffix='Retrieve Profile')
    def profile(self, request):
        """
        Retrieve profile using its video client identity
        <pre><code>
        GET: /twilio/profile?identity=7c6ca4737db3447f936037374473e61f
        </code></pre>

        ###REQUIRES AUTH

        ###Response
        Profile Object

        ---
        serializer: ProfileSerializer
        parameters:
            - name: identity
              description: Video client identity
              paramType: query
        """
        identity = request.query_params.get('identity')
        if not identity:
            raise RequiredParameter('identity')

        try:
            video_client = VideoClient.objects.get(id=identity)
        except VideoClient.DoesNotExist:
            msg = "Profile with identity %s doesn't exist" % identity
            raise InvalidParameter('identity', message=msg)
        except ValueError:
            msg = "Invalid identity"
            raise InvalidParameter('identity', message=msg)

        res = ProfileSerializer(video_client.user, context={'request': request}).data
        return Response(res)
