# -*- coding: utf-8 -*-
"""

"""
from __future__ import unicode_literals

from rest_framework import permissions, viewsets, filters, mixins
from rest_framework.response import Response
from rest_framework.decorators import detail_route

from shoutit.controllers import notifications_controller

from shoutit.models import Message, Conversation, Notification
from shoutit.api.v2.permissions import IsContributor, IsOwnerOrReadOnly, IsOwnerOrContributorsReadOnly
from shoutit.api.renderers import render_conversation, render_message, render_notification


class NotificationViewSet(viewsets.GenericViewSet):
    """
    API endpoint that allows notifications to be listed or read.
    """
    lookup_field = 'id'
    lookup_value_regex = '[0-9a-f-]{32,36}'
    # serializer_class = UserSerializer2

    filter_backends = (filters.DjangoFilterBackend, filters.SearchFilter)
    filter_fields = ('id',)
    search_fields = ('id',)

    permission_classes = (permissions.IsAuthenticated, IsContributor)

    def get_queryset(self):
        return Notification.objects.all()

    def list(self, request, *args, **kwargs):
        """
        get signed in user notifications
        """
        notifications = notifications_controller.get_user_notifications(request.user)
        ret = {
            "results": [render_notification(notification) for notification in notifications]
        }
        return Response(ret)

    @detail_route(methods=['post'])
    def read(self, request, *args, **kwargs):
        """
        mark notification as read
        """
        return Response()