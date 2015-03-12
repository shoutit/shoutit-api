# -*- coding: utf-8 -*-
"""

"""
from __future__ import unicode_literals

from rest_framework import permissions, viewsets, status, mixins
from rest_framework.response import Response
from rest_framework.decorators import detail_route, list_route
from shoutit.api.v2.pagination import ReverseDateTimePagination
from shoutit.api.v2.serializers import NotificationSerializer
from shoutit.controllers import notifications_controller


class NotificationViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    """
    Notification API Resource.
    """
    lookup_field = 'id'
    lookup_value_regex = '[0-9a-f-]{32,36}'

    serializer_class = NotificationSerializer

    pagination_class = ReverseDateTimePagination

    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        return self.request.user.notifications.all().order_by('-created_at')

    def list(self, request, *args, **kwargs):
        """
        Get signed in user notifications
        """
        notifications_controller.mark_all_as_read(request.user)
        return super(NotificationViewSet, self).list(request, *args, **kwargs)

    @list_route(methods=['post'])
    def reset(self, request, *args, **kwargs):
        """
        Mark all notification as read

        ---
        omit_serializer: true
        omit_parameters:
            - form
        """
        notifications_controller.mark_all_as_read(request.user)
        return Response(status.HTTP_204_NO_CONTENT)

    @detail_route(methods=['post', 'delete'])
    def read(self, request, *args, **kwargs):
        """
        Mark notification as read/unread

        ###Read
        <pre><code>
        POST: /api/v2/notifications/{id}/read
        </code></pre>

        ###Unread
        <pre><code>
        DELETE: /api/v2/notification/{id}/read
        </code></pre>

        ---
        omit_serializer: true
        omit_parameters:
            - form
        """
        notification = self.get_object()
        if request.method == 'POST':
            notification.is_read = True
            notification.save()
        else:
            notification.is_read = False
            notification.save()
        serializer = self.get_serializer(notification)
        return Response(serializer.data)