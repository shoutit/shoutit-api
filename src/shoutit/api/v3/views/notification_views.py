# -*- coding: utf-8 -*-
"""

"""
from __future__ import unicode_literals

from rest_framework import permissions, viewsets, status, mixins
from rest_framework.decorators import detail_route, list_route
from rest_framework.response import Response

from common.constants import NOTIFICATION_TYPE_MESSAGE
from shoutit.controllers import notifications_controller
from ..pagination import ReverseDateTimePagination
from ..serializers import NotificationSerializer
from ..views.viewsets import UUIDViewSetMixin


class NotificationViewSet(UUIDViewSetMixin, mixins.ListModelMixin, viewsets.GenericViewSet):
    """
    Notification API Resource.
    """
    serializer_class = NotificationSerializer
    pagination_class = ReverseDateTimePagination
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        return self.request.user.notifications.all().exclude(type=NOTIFICATION_TYPE_MESSAGE).order_by('-created_at')

    def list(self, request, *args, **kwargs):
        """
        List the user notifications.
        ###REQUIRES AUTH
        [Notifications Pagination](https://github.com/shoutit/shoutit-api/wiki/Notifications)
        ---
        parameters:
            - name: before
              description: timestamp to get notifications before
              paramType: query
            - name: after
              description: timestamp to get notifications after
              paramType: query
        """
        return super(NotificationViewSet, self).list(request, *args, **kwargs)

    @list_route(methods=['post'])
    def reset(self, request, *args, **kwargs):
        """
        Mark all notification as read
        ###REQUIRES AUTH
        ---
        omit_serializer: true
        omit_parameters:
            - form
        """
        notifications_controller.mark_all_as_read(request.user)
        return Response(status=status.HTTP_202_ACCEPTED)

    @detail_route(methods=['post'])
    def read(self, request, *args, **kwargs):
        """
        Mark a notification as read
        ###REQUIRES AUTH
        <pre><code>
        POST: /notifications/{id}/read
        </code></pre>

        ---
        omit_serializer: true
        omit_parameters:
            - form
        """
        notification = self.get_object()
        notification.is_read = True
        notification.save()
        serializer = self.get_serializer(notification)
        return Response(serializer.data, status=status.HTTP_202_ACCEPTED)
