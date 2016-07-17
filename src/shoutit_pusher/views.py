# -*- coding: utf-8 -*-
"""

"""
from __future__ import unicode_literals

import uuid

from rest_framework import viewsets
from rest_framework.decorators import list_route
from rest_framework.exceptions import ValidationError
from rest_framework.parsers import FormParser
from rest_framework.response import Response

from shoutit.api.parsers import ShoutitJSONParser
from shoutit.api.v2 import serializers as v2_serializers
from shoutit.api.v3 import serializers as v3_serializers
from shoutit.utils import debug_logger, create_fake_request, error_logger
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
        user = request.user
        page_admin_user = getattr(request, 'page_admin_user', None)
        authorized = page_admin_user or user
        channel = request.data.get('channel_name', '')
        # Todo: check if the user is allowed to subscribe to the channel
        socket_id = request.data.get('socket_id', '')
        api_version = request.version
        data = {
            'v2': {
                'user_id': authorized.pk,
                'user': v2_serializers.UserSerializer(authorized, context={'request': create_fake_request('v2')}).data
            },
            'v3': {
                'user_id': authorized.pk,
                'profile': v3_serializers.ProfileSerializer(authorized,
                                                            context={'request': create_fake_request('v3')}).data
            }
        }
        custom_data = data[api_version]
        try:
            auth = pusher.authenticate(channel=channel, socket_id=socket_id, custom_data=custom_data)
        except ValueError as e:
            raise ValidationError(str(e))
        debug_logger.debug("Authorized %s to subscribe to %s on %s Pusher on socket_id: %s" % (authorized, channel,
                                                                                               api_version, socket_id))
        return Response(auth)

    @list_route(methods=['post'], permission_classes=(), suffix='Webhook')
    def webhook(self, request):
        """
        Receive webhooks from Pusher.
        ###Not used directly by API clients.
        """
        try:
            webhook = pusher.validate_webhook(key=request.META.get('HTTP_X_PUSHER_KEY'),
                                              signature=request.META.get('HTTP_X_PUSHER_SIGNATURE'),
                                              body=getattr(request, 'raw_body', ''))
        except TypeError as e:
            error_logger.exception("Bad data for pusher webhook")
            raise ValidationError(str(e))
        if webhook:
            events = webhook.get('events', [])
            events.sort(key=lambda ev: ev.get('name'))
            for event in events:
                event_name = event.get('name')
                channel_name = event.get('channel')
                user_id = event.get('user_id')
                try:
                    uuid.UUID(user_id)
                except ValueError:
                    error_logger.warning("Ignored user_id: %s sent from Pusher" % user_id)
                if event_name == 'channel_occupied':
                    create_channel(channel_name)
                elif event_name == 'channel_vacated':
                    delete_channel(channel_name)
                elif event_name == 'member_added':
                    add_member(channel_name, user_id)
                elif event_name == 'member_removed':
                    remove_member(channel_name, user_id)
        return Response({'status': 'OK'})
