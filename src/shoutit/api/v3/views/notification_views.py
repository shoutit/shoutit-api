# -*- coding: utf-8 -*-
"""

"""
from rest_framework import permissions, viewsets, status, mixins
from rest_framework.decorators import detail_route, list_route
from rest_framework.response import Response

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
        return self.request.user.actual_notifications

    def list(self, request, *args, **kwargs):
        """
        List profile notifications.
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
        Mark all notifications as read
        ###REQUIRES AUTH
        ---
        omit_serializer: true
        omit_parameters:
            - form
        """
        notifications_controller.mark_actual_notifications_as_read(request.user)
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
        notification.mark_as_read()
        return Response(status=status.HTTP_202_ACCEPTED)
