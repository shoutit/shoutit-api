# -*- coding: utf-8 -*-
"""

"""
from __future__ import unicode_literals
from collections import OrderedDict

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


class ShoutViewSet(viewsets.ModelViewSet):
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
            - name: down_left_lat
              description: -90 to 90, can not be greater than up_right_lat
              paramType: query
            - name: down_left_lng
              description: -180 to 180, can not be greater than up_right_lng
              paramType: query
            - name: up_right_lat
              description: -90 to 90
              paramType: query
            - name: up_right_lng
              description: -180 to 180
              paramType: query
            - name: tags
              description: space or comma separated tags. returned shouts will contain ALL of them
              paramType: query
        """
        errors = OrderedDict()
        down_left_lat = float(request.query_params.get('down_left_lat', -90))
        down_left_lng = float(request.query_params.get('down_left_lng', -180))
        up_right_lat = float(request.query_params.get('up_right_lat', 90))
        up_right_lng = float(request.query_params.get('up_right_lng', 180))
        if down_left_lat > up_right_lat or not (90 >= down_left_lat >= -90):
            errors['down_left_lat'] = "should be between -90 and 90, also not greater than 'up_right_lat'"
        if down_left_lng > up_right_lng or not (180 >= down_left_lng >= -180):
            errors['down_left_lng'] = "should be between -180 and 180, also not greater than 'up_right_lng'"
        if not (90 >= up_right_lat >= -90):
            errors['up_right_lat'] = "should be between -90 and 90"
        if not (180 >= up_right_lng >= -180):
            errors['up_right_lng'] = "should be between -180 and 180"
        if errors:
            raise ValidationError(errors)

        return super(ShoutViewSet, self).list(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        """
        Create shout

        ###Request
        <pre><code>
        {
          "type": "offer", // `offer` or `request`
          "title": "macbook pro 15",
          "text": "apple macbook pro 15-inch in good condition for sale.",
          "price": 1000,
          "currency": "EUR",
          "images": [], // image urls
          "videos": [], // {Video Object}
          "tags": [{"name":"macbook-pro"}, {"name":"apple"}, {"name":"used"}],
          "location": {
            "country": "AE",
            "city": "Dubai",
            "latitude": 25.165173368664,
            "longitude": 55.2667236328125
          }
        }
        </code></pre>
        ---
        omit_serializer: true
        omit_parameters:
            - form
        parameters:
            - name: body
              paramType: body
        """
        return super(ShoutViewSet, self).create(request, *args, **kwargs)

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
        return super(ShoutViewSet, self).retrieve(request, *args, **kwargs)

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

    @detail_route(methods=['post'])
    def reply(self, request, *args, **kwargs):
        """
        Reply to a shout
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
        return Response()
