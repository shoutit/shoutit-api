# -*- coding: utf-8 -*-
"""

"""
from __future__ import unicode_literals

from rest_framework import permissions, viewsets, status, mixins
from rest_framework.response import Response
from rest_framework.decorators import detail_route, list_route
from shoutit.api.v2.pagination import ReverseDateTimePagination
from shoutit.api.v2.serializers import NotificationSerializer
from shoutit.api.v2.views.viewsets import UUIDViewSetMixin
from shoutit.controllers import notifications_controller


class NotificationViewSet(UUIDViewSetMixin, mixins.ListModelMixin, viewsets.GenericViewSet):
    """
    Notification API Resource.
    """
    serializer_class = NotificationSerializer

    pagination_class = ReverseDateTimePagination

    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        return self.request.user.notifications.all().order_by('-created_at')

    def list(self, request, *args, **kwargs):
        """
        Get signed in user notifications

        [Notifications Pagination](https://docs.google.com/document/d/1Zp9Ks3OwBQbgaDRqaULfMDHB-eg9as6_wHyvrAWa8u0/edit#heading=h.ix2g5tgh1m27)
        ---
        parameters:
            - name: before
              description: timestamp to get notifications before
              paramType: query
            - name: after
              description: timestamp to get notifications after
              paramType: query
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
        POST: /v2/notifications/{id}/read
        </code></pre>

        ###Unread
        <pre><code>
        DELETE: /v2/notification/{id}/read
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