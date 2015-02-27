# -*- coding: utf-8 -*-
"""

"""
from __future__ import unicode_literals

from rest_framework import permissions, viewsets, filters, status
from rest_framework.response import Response
from rest_framework.decorators import detail_route
from shoutit.api.v2.serializers import NotificationSerializer
from shoutit.controllers import notifications_controller


class NotificationViewSet(viewsets.GenericViewSet):
    """
    Notification API Resource.
    """
    lookup_field = 'id'
    # lookup_value_regex = '[0-9a-f-]{32,36}'
    serializer_class = NotificationSerializer

    filter_backends = (filters.DjangoFilterBackend,)
    filter_fields = ('id',)

    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        return self.request.user.notifications.all().order_by('-created_at')

    def list(self, request, *args, **kwargs):
        """
        Get signed in user notifications
        """
        notifications = self.get_queryset()
        page = self.paginate_queryset(notifications)
        serializer = self.get_pagination_serializer(page)
        notification_ids = [notification['id'] for notification in serializer.data['results']]
        notifications_controller.mark_notifications_as_read_by_ids(notification_ids)
        return Response(serializer.data)

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