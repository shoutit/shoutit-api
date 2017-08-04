# -*- coding: utf-8 -*-
"""

"""
from collections import OrderedDict
from datetime import timedelta

from common.constants import SMSInvitationStatus
from django.db.models import Count
from django.utils.timezone import now
from rest_framework import status, mixins, viewsets
from rest_framework import permissions
from rest_framework.decorators import list_route
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from shoutit.models import SMSInvitation
from . import DEFAULT_PARSER_CLASSES_v2
from ..serializers import SMSInvitationSerializer
from ..views.viewsets import UUIDViewSetMixin


class SMSViewSet(UUIDViewSetMixin, mixins.RetrieveModelMixin, mixins.CreateModelMixin, viewsets.GenericViewSet):
    """
    SMSInvitation API Resources.
    """
    parser_classes = DEFAULT_PARSER_CLASSES_v2
    queryset = SMSInvitation.objects.all()
    serializer_class = SMSInvitationSerializer
    permission_classes = (permissions.IsAuthenticated,)

    @list_route(methods=['get'], permission_classes=(permissions.IsAdminUser,), suffix='Summary')
    def summary(self, request, *args, **kwargs):
        """
        SMSInvitation summary
        ---
        omit_serializer: true
        omit_parameters:
            - query
        """
        countries = request.query_params.get('countries', '').split(',')
        today_eod = now().replace(hour=23, minute=59, second=59, microsecond=999999)
        periods = [(1, 'day'), (7, 'week'), (30, 'month')]
        if countries == ['']:
            month_ago = today_eod - timedelta(days=periods[-1][0])
            countries = list(SMSInvitation.objects.filter(modified_at__gt=month_ago)
                             .values_list('country', flat=True).distinct())
        statuses = SMSInvitationStatus.choices + ((None, 'total'),)

        def _status_summary(sms_status, days):
            modified_at = today_eod - timedelta(days=days)
            invitations_qs = SMSInvitation.objects.filter(country__in=countries, modified_at__gt=modified_at)
            if sms_status is not None:
                invitations_qs = invitations_qs.filter(status=sms_status)
            invitations = invitations_qs.values('country').annotate(count=Count('country'))
            result = OrderedDict([(invitation['country'], invitation['count']) for invitation in invitations])
            result['total'] = invitations_qs.count()
            return result

        results = OrderedDict(
            [(p[1], OrderedDict([(s[1], _status_summary(s[0], p[0])) for s in statuses])) for p in periods]
        )
        return Response(results)

    def create(self, request, *args, **kwargs):
        """
        Create SMSInvitation
        ---
        omit_serializer: true
        """
        serializer = self.get_serializer(data=request.data)
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
            serializer = self.get_serializer(data=item)
            try:
                serializer.is_valid(raise_exception=True)
                serializer.save()
            except ValidationError:
                items.remove(item)
        return Response({'added': len(items)}, status=status.HTTP_201_CREATED)
