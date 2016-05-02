"""

"""
from __future__ import unicode_literals

import uuid

from twilio.access_token import AccessToken, ConversationsGrant

from .models import VideoClient
from .settings import SHOUTIT_TWILIO_SETTINGS


def create_video_client(user):
    # Create identity for the token using random uuid.hex (not to have the hyphens)
    identity = uuid.uuid4().hex

    # Create an Access Token
    token = AccessToken(SHOUTIT_TWILIO_SETTINGS['TWILIO_ACCOUNT_SID'], SHOUTIT_TWILIO_SETTINGS['TWILIO_API_KEY'],
                        SHOUTIT_TWILIO_SETTINGS['TWILIO_API_SECRET'], identity=identity,
                        ttl=SHOUTIT_TWILIO_SETTINGS['ttl'])

    # Grant access to Conversations
    grant = ConversationsGrant(configuration_profile_sid=SHOUTIT_TWILIO_SETTINGS['TWILIO_CONFIGURATION_SID'])
    token.add_grant(grant)

    # Create VideoClient
    jwt_token = token.to_jwt()
    video_client = VideoClient.create(id=identity, user=user, token=jwt_token)

    return video_client
