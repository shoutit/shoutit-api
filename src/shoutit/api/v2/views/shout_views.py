# -*- coding: utf-8 -*-
"""

"""
from __future__ import unicode_literals

from rest_framework import permissions, viewsets, filters, mixins, generics
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.decorators import detail_route, list_route
from rest_framework.settings import api_settings
from shoutit.api.v2.filters import ShoutFilter
from shoutit.api.v2.serializers import TradeSerializer


from shoutit.models import  Trade
from shoutit.api.v2.permissions import IsContributor, IsOwnerOrReadOnly, IsOwnerOrContributorsReadOnly
from shoutit.api.renderers import render_conversation, render_message, render_shout


class ShoutViewSet(viewsets.GenericViewSet):
    """
    Shout API Resource
    """
    lookup_field = 'id'
    lookup_value_regex = '[0-9a-f-]{32,36}'

    serializer_class = TradeSerializer

    def get_queryset(self):
        return Trade.objects.get_valid_trades().all()

    filter_backends = (filters.DjangoFilterBackend, filters.SearchFilter)
    filter_class = ShoutFilter
    search_fields = ('=id', 'item__name', 'text', 'tags__name')

    def list(self, request, *args, **kwargs):
        """
        Get shouts based on filters
        ---
        omit_serializer: true
        parameters:
            - name: search
              description: space or comma separated keywords to search in title, text, tags
              paramType: query
            - name: type
              paramType: query
              defaultValue: all
              enum:
                - all
                - offers
                - requests
            - name: country
              paramType: query
            - name: city
              paramType: query
            - name: min_price
              paramType: query
            - name: max_price
              paramType: query
            - name: tags
              description: space or comma separated tags. returned shouts will contain ALL of them
              paramType: query
        """
        instance = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(instance)
        serializer = self.get_pagination_serializer(page)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        """
        create shout
        """
        return Response()

    def retrieve(self, request, *args, **kwargs):
        """
        get shout
        """
        shout = self.get_object()
        return Response(render_shout(shout))

    def update(self, request, *args, **kwargs):
        """
        modify shout
        """
        shout = self.get_object()
        return Response(render_shout(shout))

    def destroy(self, request, *args, **kwargs):
        """
        delete shout
        """
        shout = self.get_object()
        return Response()

    @list_route(methods=['get'])
    def nearby(self, request, *args, **kwargs):
        """
        get nearby shouts
        """
        return Response()

    @detail_route(methods=['post'])
    def reply(self, request, *args, **kwargs):
        """
        reply to a shout
        """
        return Response()
