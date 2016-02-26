# -*- coding: utf-8 -*-
"""

"""
from __future__ import unicode_literals

from rest_framework import viewsets
from rest_framework.decorators import list_route
from rest_framework.response import Response
from twilio.access_token import AccessToken, ConversationsGrant

from .settings import SHOUTIT_TWILIO_SETTINGS


class ShoutitTwilioViewSet(viewsets.ViewSet):
    """
    Shoutit Twilio API Resources.
    """

    @list_route(methods=['post'], suffix='Authorize')
    def video_auth(self, request):
        """
        Create a video chat endpoint.
        ###REQUIRES AUTH
        ###Response
        <pre><code>
        {
          "token": "eyJhbGciOiAiSFMyNTYiLCAidHlwIjogIkpXVCIsICJjdHkiOiAidHdpbGlvLWZwYTt2PTEifQ.eyJpc3MiOiAiU0s3MDFlYzE",
          "identity": "17729791284"
        }
        </code></pre>
        ---
        """

        # Get credentials
        account_sid = SHOUTIT_TWILIO_SETTINGS['TWILIO_ACCOUNT_SID']
        api_key = SHOUTIT_TWILIO_SETTINGS['TWILIO_API_KEY']
        api_secret = SHOUTIT_TWILIO_SETTINGS['TWILIO_API_SECRET']

        # Create an Access Token
        token = AccessToken(account_sid, api_key, api_secret)

        # Set the Identity of this token
        token.identity = request.user.username

        # Grant access to Conversations
        grant = ConversationsGrant()
        grant.configuration_profile_sid = SHOUTIT_TWILIO_SETTINGS['TWILIO_CONFIGURATION_SID']
        token.add_grant(grant)

        # Return token info
        res = {
            'identity': token.identity,
            'token': token.to_jwt()
        }
        return Response(res)
