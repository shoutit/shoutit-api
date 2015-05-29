# -*- coding: utf-8 -*-
"""

"""
from __future__ import unicode_literals
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.decorators import list_route
from .utils import pusher


class ShoutitPusherViewSet(viewsets.ViewSet):
    """
    Shoutit Pusher API Resources.
    """

    @list_route(methods=['post'], suffix='Authorize')
    def auth(self, request):
        """
        Authorize channel subscriptions
        ---
        """
        channel = request.data.get('channel_name', '')
        socket_id = request.data.get('socket_id', '')
        try:
            auth = pusher.authenticate(channel=channel, socket_id=socket_id)
        except ValueError as e:
            auth = {'error': str(e)}
        return Response(auth)
