# -*- coding: utf-8 -*-
"""

"""
from __future__ import unicode_literals
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.decorators import list_route
from shoutit.api.v2.serializers import UserSerializer
from shoutit.utils import debug_logger
from .utils import pusher
from .controllers import add_member, remove_member, create_channel, delete_channel


class ShoutitPusherViewSet(viewsets.ViewSet):
    """
    Shoutit Pusher API Resources.
    """

    @list_route(methods=['post'], suffix='Authorize')
    def auth(self, request):
        """
        Authorize channel subscriptions.
        ###Not used directly by API clients.
        ---
        """
        channel = request.data.get('channel_name', '')
        socket_id = request.data.get('socket_id', '')
        custom_data = {
            'user_id': request.user.pk,
            'user': UserSerializer(request.user, context={'request': request}).data
        }
        try:
            auth = pusher.authenticate(channel=channel, socket_id=socket_id, custom_data=custom_data)
        except ValueError as e:
            auth = {'error': str(e)}
        return Response(auth)

    @list_route(methods=['post'], permission_classes=(), suffix='Webhook')
    def webhook(self, request):
        """
        Receive webhooks from Pusher.
        ###Not used directly by API clients.
        """
        webhook = pusher.validate_webhook(key=request.META.get('HTTP_X_PUSHER_KEY'),
                                          signature=request.META.get('HTTP_X_PUSHER_SIGNATURE'),
                                          body=request.body)
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
