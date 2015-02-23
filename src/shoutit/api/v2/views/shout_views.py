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
        Get shout

        ###Shout Object
        <pre><code>
        {
          "id": "fc598c12-f7b6-4a24-b56e-defd6178876e",
          "api_url": "http://shoutit.dev:8000/api/v2/shouts/fc598c12-f7b6-4a24-b56e-defd6178876e",
          "web_url": "",
          "type": "offer",
          "title": "offer 1",
          "text": "selling some stuff",
          "price": 1,
          "currency": "AED",
          "thumbnail": null,
          "images": "[]", // list of urls
          "videos": [],  // list of {Video Object}
          "tags": [],  // list of {Tag Object}
          "location": {
            "country": "AE",
            "city": "Dubai",
            "latitude": 25.165173368664,
            "longitude": 55.2667236328125
          },
          "user": {}, // {User Object}
          "date_published": 1424481256
        }
        </code></pre>
        ---
        omit_serializer: true
        """
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def update(self, request, *args, **kwargs):
        """
        Modify shout

        ```
        NOT IMPLEMENTED!
        ```
        ---
        omit_serializer: true
        omit_parameters:
            - form
        parameters:
            - name: body
              paramType: body
        """
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        """
        Delete shout

        ```
        NOT IMPLEMENTED!
        ```
        ---
        omit_serializer: true
        omit_parameters:
            - form
        """
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @list_route(methods=['get'])
    def nearby(self, request, *args, **kwargs):
        """
        Get nearby shouts
        """
        return Response()

    @detail_route(methods=['post'])
    def reply(self, request, *args, **kwargs):
        """
        Reply to a shout
        ---
        omit_serializer: true
        omit_parameters:
            - form
        parameters:
            - name: body
              paramType: body
        """
        return Response()
