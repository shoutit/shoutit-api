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
    def shouts_sort_types(self, request):
        """
        Get shouts sort types
        ---
        """
        return Response([
            {'type': 'time', 'name': 'Latest'},
            {'type': 'distance', 'name': 'Nearest'},
            {'type': 'price_asc', 'name': 'Price Increasing'},
            {'type': 'price_desc', 'name': 'Price Decreasing'},
            {'type': 'recommended', 'name': 'Recommended'},
        ])

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

        ###Reporting Shout
        <pre><code>
        {
            "text": "the reason of this report, any text.",
            "attached_object": {
                "shout": {
                    "id": ""
                }
            }
        }
        </code></pre>

        ###Reporting User
        <pre><code>
        {
            "text": "the reason of this report, any text.",
            "attached_object": {
                "user": {
                    "id": ""
                }
            }
        }
        </code></pre>

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
