# -*- coding: utf-8 -*-
"""

"""
from __future__ import unicode_literals

from rest_framework import filters, status, mixins, viewsets
from rest_framework.decorators import list_route
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from django.conf import settings

from shoutit.models import SMSInvitation
from ..pagination import ShoutitPageNumberPagination
from ..serializers import SMSInvitationSerializer
from ..views.viewsets import UUIDViewSetMixin


class SMSViewSet(UUIDViewSetMixin, mixins.ListModelMixin, mixins.RetrieveModelMixin, mixins.CreateModelMixin,
                 mixins.DestroyModelMixin, viewsets.GenericViewSet):
    """
    SMSInvitation API Resources.
    """
    parser_classes = settings.REST_FRAMEWORK['DEFAULT_PARSER_CLASSES_v2']
    queryset = SMSInvitation.objects.all().order_by('-created_at')
    serializer_class = SMSInvitationSerializer
    filter_backends = (filters.DjangoFilterBackend,)
    filter_fields = ('status', 'country', 'mobile')
    pagination_class = ShoutitPageNumberPagination
    permission_classes = ()

    # Todo: add some kind of authentication to all methods

    def retrieve(self, request, *args, **kwargs):
        """
        Get an SMSInvitation
        ---
        omit_serializer: true
        """
        return super(SMSViewSet, self).retrieve(request, *args, **kwargs)

    def list(self, request, *args, **kwargs):
        """
        List SMSInvitations
        ---
        omit_serializer: true
        omit_parameters:
            - query
        """
        return super(SMSViewSet, self).list(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        """
        Create SMSInvitation
        ---
        omit_serializer: true
        """
        serializer = SMSInvitationSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    @list_route(methods=['post'], suffix='Bulk Create')
    def bulk_create(self, request, *args, **kwargs):
        """
        Create Bulk SMSInvitations
        ---
        omit_serializer: true
        """
        items = request.data
        for item in items[:]:
            serializer = SMSInvitationSerializer(data=item, context={'request': request})
            try:
                serializer.is_valid(raise_exception=True)
                serializer.save()
            except ValidationError:
                items.remove(item)
        return Response({'added': len(items)}, status=status.HTTP_201_CREATED)

    def partial_update(self, request, *args, **kwargs):
        """
        Modify an SMSInvitation
        ---
        omit_serializer: true
        """
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        """
        Delete an SMSInvitation
        ###NOT ALLOWED
        ---
        omit_serializer: true
        """
        return Response("Not allowed", status=status.HTTP_406_NOT_ACCEPTABLE)
