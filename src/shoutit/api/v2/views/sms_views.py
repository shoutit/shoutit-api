# -*- coding: utf-8 -*-
"""

"""
from __future__ import unicode_literals
from rest_framework import filters, status
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from rest_framework.decorators import list_route
from shoutit.api.v2.pagination import ShoutitPageNumberPagination
from shoutit.api.v2.serializers import SMSInvitationSerializer
from shoutit.api.v2.views.viewsets import NoUpdateModelViewSet, UUIDViewSetMixin
from shoutit.models import SMSInvitation


class SMSViewSet(UUIDViewSetMixin, NoUpdateModelViewSet):
    """
    SMS API Resources.
    """
    queryset = SMSInvitation.objects.all().order_by('-modified_at')
    serializer_class = SMSInvitationSerializer
    filter_backends = (filters.DjangoFilterBackend,)
    filter_fields = ('status', 'country', 'mobile')
    pagination_class = ShoutitPageNumberPagination
    permission_classes = ()

    def list(self, request, *args, **kwargs):
        """
        Get SMS Invitations
        """
        return super(SMSViewSet, self).list(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        """
        Create SMS Invitation
        """
        serializer = SMSInvitationSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    @list_route(methods=['post'], suffix='Bulk Create')
    def bulk_create(self, request, *args, **kwargs):
        """
        Create Bulk SMS Invitations
        """
        items = request.data
        for item in items[:]:
            serializer = SMSInvitationSerializer(data=item, context={'request': request})
            try:
                serializer.is_valid(raise_exception=True)
                serializer.save()
            except ValidationError as e:
                items.remove(item)
        return Response({'added': len(items)}, status=status.HTTP_201_CREATED)

    def partial_update(self, request, *args, **kwargs):
        """
        Modify SMS Invitation
        """
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
