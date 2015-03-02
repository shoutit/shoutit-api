# -*- coding: utf-8 -*-
"""

"""
from __future__ import unicode_literals

from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.decorators import list_route

from shoutit.api.v2.serializers import CategorySerializer, CurrencySerializer
from shoutit.models import Currency, Category


class MiscViewSet(viewsets.ViewSet):
    """
    Other API Resources.
    """
    @list_route(methods=['get'])
    def currencies(self, request):
        """
        Get currencies
        ---
        serializer: CurrencySerializer
        """
        currencies = Currency.objects.all()
        serializer = CurrencySerializer(currencies, many=True)
        return Response(serializer.data)

    @list_route(methods=['get'])
    def categories(self, request):
        """
        Get categories
        ---
        serializer: CategorySerializer
        """
        categories = Category.objects.all()
        serializer = CategorySerializer(categories, many=True)
        return Response(serializer.data)
