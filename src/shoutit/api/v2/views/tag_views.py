# -*- coding: utf-8 -*-
"""

"""
from __future__ import unicode_literals

from rest_framework import permissions, viewsets, filters, status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.decorators import detail_route

from shoutit.api.v2.mixins import CustomPaginationSerializerMixin
from shoutit.controllers import stream_controller

from shoutit.models import User, Tag
from shoutit.api.v2.serializers import TagSerializer, UserSerializer, TradeSerializer
from shoutit.api.v2.permissions import IsOwnerOrReadOnly


class TagViewSet(CustomPaginationSerializerMixin, viewsets.GenericViewSet):
    """
    Tag API Resource.
    """
    lookup_field = 'name'
    lookup_value_regex = '[a-z0-9-]{2,30}'

    serializer_class = TagSerializer

    queryset = Tag.objects.all()

    filter_backends = (filters.DjangoFilterBackend, filters.SearchFilter)
    filter_fields = ('name',)
    search_fields = ('=id', 'name')

    def list(self, request, *args, **kwargs):
        """
        Get tags based on `search` query param.

        ###Tag Object
        <pre><code>
        {
          "id": "a45c843f-8473-2135-bde4-0236754f151d",
          "name": "computer-games",
          "api_url": "http://shoutit.dev:8000/api/v2/tags/computer-games",
          "web_url": "http://shoutit.dev:8000/tag/computer-games",
          "is_listening": true,
          "listeners_count": 321
        }
        </code></pre>

        ###Response
        <pre><code>
        {
          "count": 4, // number of results
          "next": null, // next results page url
          "previous": null, // previous results page url
          "results": [] // list of {Tag Object} as described above
        }
        </code></pre>
        ---
        omit_serializer: true
        parameters:
            - name: search
              paramType: query
            - name: type
              paramType: query
              defaultValue: all
              enum:
                - all
                - top
                - featured
            - name: country
              description: only used when type is `featured` or `top`
              paramType: query
            - name: city
              description: only used when type is `featured` or `top`
              paramType: query
        """

        tag_type = request.query_params.get('type', 'all')
        if tag_type not in ['all', 'top', 'featured']:
            raise ValidationError({'type': "should be `all`, `top` or `featured`."})

        tag_country = request.query_params.get('country', None)
        tag_city = request.query_params.get('city', None)
        # todo: filter on country, city, top, featured

        instance = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(instance)
        serializer = self.get_pagination_serializer(page)
        return Response(serializer.data)

    def retrieve(self, request, *args, **kwargs):
        """
        Get tag
        ---
        omit_serializer: true
        """
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @detail_route(methods=['post', 'delete'])
    def listen(self, request, *args, **kwargs):
        """
        Start/Stop listening to tag

        ###Listen
        <pre><code>
        POST: /api/v2/tags/{name}/listen
        </code></pre>

        ###Stop listening
        <pre><code>
        DELETE: /api/v2/tags/{name}/listen
        </code></pre>
        ---
        omit_serializer: true
        omit_parameters:
            - form
        """
        tag = self.get_object()

        if request.method == 'POST':
            stream_controller.listen_to_stream(request.user, tag.stream2)
            msg = "you started listening to {} shouts.".format(tag.name)

        else:
            stream_controller.remove_listener_from_stream(request.user, tag.stream2)
            msg = "you stopped listening to {} shouts.".format(tag.name)

        ret = {
            'data': {'success': msg},
            'status': status.HTTP_201_CREATED if request.method == 'POST' else status.HTTP_202_ACCEPTED
        }

        return Response(**ret)

    @detail_route(methods=['get'])
    def listeners(self, request, *args, **kwargs):
        """
        Get tag listeners

        ###Response
        <pre><code>
        {
          "count": 4, // number of results
          "next": null, // next results page url
          "previous": null, // previous results page url
          "results": [] // list of {User Object} as described above
        }
        </code></pre>
        ---
        omit_serializer: true
        omit_parameters:
            - form
        parameters:
            - name: page
              paramType: query
        """
        tag = self.get_object()
        listeners = stream_controller.get_stream_listeners(tag.stream2)
        page = self.paginate_queryset(listeners)
        serializer = self.get_custom_pagination_serializer(page, UserSerializer)
        return Response(serializer.data)

    @detail_route(methods=['get'])
    def shouts(self, request, *args, **kwargs):
        """
        Get tag shouts

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

        ###Response
        <pre><code>
        {
          "count": 4, // number of results
          "next": null, // next results page url
          "previous": null, // previous results page url
          "results": [] // list of {Shout Object} as described above
        }
        </code></pre>
        ---
        omit_serializer: true
        omit_parameters:
            - form
        parameters:
            - name: type
              paramType: query
              required: true
              defaultValue: all
              enum:
                - requests
                - offers
                - all
            - name: page
              paramType: query
        """
        shout_type = request.query_params.get('type', 'all')
        if shout_type not in ['offers', 'requests', 'all']:
            raise ValidationError({'type': "should be `offers`, `requests` or `all`."})

        tag = self.get_object()
        trades = stream_controller.get_stream2_trades_qs(tag.stream2, shout_type)
        page = self.paginate_queryset(trades)
        serializer = self.get_custom_pagination_serializer(page, TradeSerializer)
        return Response(serializer.data)
