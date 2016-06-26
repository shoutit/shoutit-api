# -*- coding: utf-8 -*-
"""

"""
from __future__ import unicode_literals

from collections import OrderedDict

from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from rest_framework import viewsets
from rest_framework.decorators import list_route
from rest_framework.response import Response

from shoutit.api.v3.exceptions import ShoutitBadRequest, RequiredParameter, InvalidParameter, RequiredBody
from shoutit.api.v3.serializers import ProfileSerializer
from shoutit.controllers import notifications_controller
from shoutit.models import User
from .controllers import create_video_client
from .models import VideoClient


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
        # Todo: Move the logic to Serializer
        user = request.user
        try:
            video_client = user.video_client

            # Check whether client has an expired token
            if timezone.now() > video_client.expires_at:
                video_client.delete()
                raise ValueError()
        except (AttributeError, ValueError):
            try:
                video_client = create_video_client(user)
            except (ValidationError, IntegrityError) as e:
                msg = _("Couldn't authorize you to make video calls")
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
        # Todo: Move the logic to Serializer

        other_username = request.query_params.get('profile')
        if not other_username:
            raise RequiredParameter('profile')
        if other_username == request.user.username:
            raise InvalidParameter('profile', "You can't call your self")

        try:
            other_user = User.objects.get(username=other_username)
        except User.DoesNotExist:
            msg = _("Profile with username '%(username)s' does not exist") % {'username': other_username}
            raise InvalidParameter('profile', message=msg)

        if hasattr(other_user, 'video_client'):
            video_client = other_user.video_client
        else:
            # Create video client for the other user
            try:
                video_client = create_video_client(other_user)
            except (ValidationError, IntegrityError) as e:
                msg = _("Error calling %(name)s") % {'name': other_username.name}
                raise ShoutitBadRequest(message=msg, developer_message=unicode(e))

        # Notify the other user
        notifications_controller.notify_user_of_incoming_video_call(user=other_user, caller=request.user)

        res = {
            'identity': video_client.identity
        }
        return Response(res)

    @list_route(methods=['post'], suffix='Video call Profile')
    def video_call(self, request):
        """
        Send the Profile Push about video call
        ###REQUIRES AUTH
        ###Request
        <pre><code>
        {
          "identity": "7c6ca4737db3447f936037374473e61f",
          "missed": true
        }
        </code></pre>

        ---
        """
        # Todo: Move the logic to Serializer
        data = request.data
        identity = data.get('identity')
        if not identity:
            raise RequiredBody('identity')
        try:
            video_client = VideoClient.objects.get(id=identity)
        except VideoClient.DoesNotExist:
            msg = _("Profile with identity %(identity)s does not exist") % {'identity': identity}
            raise InvalidParameter('identity', message=msg)
        except ValueError:
            msg = _("Invalid identity")
            raise InvalidParameter('identity', message=msg)
        other_user = video_client.user

        missed = data.get('missed', False)

        if missed:
            # Notify the other user about the missed video call
            notifications_controller.notify_user_of_missed_video_call(user=other_user, caller=request.user)
        else:
            # Notify the other user about the incoming video call
            notifications_controller.notify_user_of_incoming_video_call(user=other_user, caller=request.user)

        return Response()

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
        # Todo: Move the logic to Serializer
        identity = request.query_params.get('identity')
        if not identity:
            raise RequiredParameter('identity')

        try:
            video_client = VideoClient.objects.get(id=identity)
        except VideoClient.DoesNotExist:
            msg = _("Profile with identity %(identity)s does not exist") % {'identity': identity}
            raise InvalidParameter('identity', message=msg)
        except ValueError:
            msg = _("Invalid identity")
            raise InvalidParameter('identity', message=msg)

        res = ProfileSerializer(video_client.user, context={'request': request}).data
        return Response(res)
