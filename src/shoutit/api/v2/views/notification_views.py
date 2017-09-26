# -*- coding: utf-8 -*-
"""

"""
from rest_framework import permissions, viewsets, status, mixins
from rest_framework.decorators import detail_route, list_route
from rest_framework.response import Response

from shoutit.controllers import notifications_controller
from . import DEFAULT_PARSER_CLASSES_v2
from ..pagination import ReverseDateTimePagination
from ..serializers import NotificationSerializer
from ..views.viewsets import UUIDViewSetMixin


class NotificationViewSet(UUIDViewSetMixin, mixins.ListModelMixin, viewsets.GenericViewSet):
    """
    Notification API Resource.
    """
    parser_classes = DEFAULT_PARSER_CLASSES_v2
    serializer_class = NotificationSerializer
    pagination_class = ReverseDateTimePagination
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        return self.request.user.notifications.all().order_by('-created_at')

    def list(self, request, *args, **kwargs):
        """
        List the user notifications.
        ###REQUIRES AUTH
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
        # Todo: send the number of unread notifications along with results
        # notifications_controller.mark_all_as_read(request.user)
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

    @detail_route(methods=['post', 'delete'])
    def read(self, request, *args, **kwargs):
        """
        Mark a notification as read/unread
        ###REQUIRES AUTH
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
        return Response(serializer.data, status=status.HTTP_202_ACCEPTED)
