# -*- coding: utf-8 -*-
"""

"""
from __future__ import unicode_literals

from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import list_route

from shoutit.api.v2.serializers import CategorySerializer, CurrencySerializer, ReportSerializer
from shoutit.models import Currency, Category


class MiscViewSet(viewsets.ViewSet):
    """
    Other API Resources.
    """

    permission_classes = ()

    @list_route(methods=['get'], suffix='Currencies')
    def currencies(self, request):
        """
        Get currencies
        ---
        serializer: CurrencySerializer
        """
        currencies = Currency.objects.all()
        serializer = CurrencySerializer(currencies, many=True, context={'request': request})
        return Response(serializer.data)

    @list_route(methods=['get'], suffix='Categories')
    def categories(self, request):
        """
        Get categories
        ---
        serializer: CategorySerializer
        """
        categories = Category.objects.all()
        serializer = CategorySerializer(categories, many=True, context={'request': request})
        return Response(serializer.data)

    @list_route(methods=['post'], suffix='Reports')
    def reports(self, request):
        """
        Report
        ---
        serializer: ReportSerializer
        omit_parameters:
            - form
        parameters:
            - name: body
              paramType: body
        """
        serializer = ReportSerializer(data=request.data, partial=True, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
