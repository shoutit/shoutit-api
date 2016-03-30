# -*- coding: utf-8 -*-
"""

"""
from __future__ import unicode_literals

from rest_framework import viewsets
from rest_framework.decorators import list_route
from rest_framework.exceptions import ValidationError
from rest_framework.parsers import FormParser
from rest_framework.response import Response

from shoutit.api.parsers import ShoutitJSONParser
from shoutit.api.v2 import serializers as v2_serializers
from shoutit.api.v3 import serializers as v3_serializers
from shoutit.utils import debug_logger, create_fake_request
from .controllers import add_member, remove_member, create_channel, delete_channel
from .utils import pusher


class ShoutitPusherViewSet(viewsets.ViewSet):
    """
    Shoutit Pusher API Resources.
    """
    parser_classes = (ShoutitJSONParser, FormParser)

    @list_route(methods=['post'], suffix='Authorize')
    def auth(self, request):
        """
        Authorize channel subscriptions.
        ###Not used directly by API clients.
        ---
        """
        channel = request.data.get('channel_name', '')
        # Todo: check if the user is allowed to subscribe to the channel
        socket_id = request.data.get('socket_id', '')
        api_version = request.version
        data = {
            'v2': {
                'user_id': request.user.pk,
                'user': v2_serializers.UserSerializer(request.user, context={'request': create_fake_request('v2')}).data
            },
            'v3': {
                'user_id': request.user.pk,
                'profile': v3_serializers.ProfileSerializer(request.user, context={'request': create_fake_request('v3')}).data
            }
        }
        custom_data = data[api_version]
        try:
            auth = pusher.authenticate(channel=channel, socket_id=socket_id, custom_data=custom_data)
        except ValueError as e:
            raise ValidationError(str(e))
        return Response(auth)

    @list_route(methods=['post'], permission_classes=(), suffix='Webhook')
    def webhook(self, request):
        """
        Receive webhooks from Pusher.
        ###Not used directly by API clients.
        """
        webhook = pusher.validate_webhook(key=request.META.get('HTTP_X_PUSHER_KEY'),
                                          signature=request.META.get('HTTP_X_PUSHER_SIGNATURE'),
                                          body=request.raw_body)
        if webhook:
            events = webhook.get('events', [])
            events.sort(key=lambda e: e.get('name'))
            for event in events:
                debug_logger.debug(event)
                event_name = event.get('name')
                channel_name = event.get('channel')
                user_id = event.get('user_id')
                if event_name == 'channel_occupied':
                    create_channel(channel_name)
                elif event_name == 'channel_vacated':
                    delete_channel(channel_name)
                elif event_name == 'member_added':
                    add_member(channel_name, user_id)
                elif event_name == 'member_removed':
                    remove_member(channel_name, user_id)
        return Response({'status': 'ok'})
