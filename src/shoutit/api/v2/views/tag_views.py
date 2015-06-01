# -*- coding: utf-8 -*-
"""

"""
from __future__ import unicode_literals

from rest_framework import permissions, viewsets, filters, status, mixins
from rest_framework.response import Response
from rest_framework.decorators import detail_route
from rest_framework_extensions.mixins import DetailSerializerMixin

from shoutit.api.v2.filters import TagFilter
from shoutit.api.v2.pagination import (
    ShoutitPageNumberPagination, ReverseDateTimePagination, PageNumberIndexPagination)
from shoutit.api.v2.serializers import *  # NOQA
from shoutit.controllers import stream_controller
from shoutit.models import ShoutIndex


class TagViewSet(DetailSerializerMixin, mixins.ListModelMixin, viewsets.GenericViewSet):
    """
    Tag API Resource.
    """
    lookup_field = 'name'

    serializer_class = TagSerializer
    serializer_detail_class = TagDetailSerializer

    queryset = Tag.objects.all()

    pagination_class = ShoutitPageNumberPagination

    filter_backends = (filters.DjangoFilterBackend, filters.SearchFilter)
    filter_class = TagFilter
    search_fields = ('=id', 'name')

    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)

    def list(self, request, *args, **kwargs):
        """
        Get tags based on `search` query param.

        ###Response
        <pre><code>
        {
          "count": 4, // number of results
          "next": null, // next results page url
          "previous": null, // previous results page url
          "results": [] // list of {Tag Object}, an extra field `title` will be returned for featured tags
        }
        </code></pre>
        ---
        serializer: TagSerializer
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
            - name: category
              description: return tags that belong to this category only
              paramType: query
        """
        tags_type = request.query_params.get('type')
        if tags_type == 'featured':
            self.serializer_class = FeaturedTagSerializer
        return super(TagViewSet, self).list(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        """
        Get tag
        ---
        serializer: TagDetailSerializer
        """
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @detail_route(methods=['post', 'delete'], suffix='Listen')
    def listen(self, request, *args, **kwargs):
        """
        Start/Stop listening to tag

        ###Listen
        <pre><code>
        POST: /v2/tags/{name}/listen
        </code></pre>

        ###Stop listening
        <pre><code>
        DELETE: /v2/tags/{name}/listen
        </code></pre>
        ---
        omit_serializer: true
        omit_parameters:
            - form
        """
        tag = self.get_object()

        if request.method == 'POST':
            stream_controller.listen_to_stream(request.user, tag.stream, request)
            msg = "you started listening to {} shouts.".format(tag.name)

        else:
            stream_controller.remove_listener_from_stream(request.user, tag.stream)
            msg = "you stopped listening to {} shouts.".format(tag.name)

        ret = {
            'data': {'success': msg},
            'status': status.HTTP_201_CREATED if request.method == 'POST' else status.HTTP_202_ACCEPTED
        }

        return Response(**ret)

    @detail_route(methods=['get'], suffix='Listeners')
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
        serializer: UserSerializer
        omit_parameters:
            - form
        parameters:
            - name: page
              paramType: query
            - name: page_size
              paramType: query
        """
        tag = self.get_object()
        listeners = stream_controller.get_stream_listeners(tag.stream)
        page = self.paginate_queryset(listeners)
        serializer = UserSerializer(page, many=True, context={'request': request})
        return self.get_paginated_response(serializer.data)

    @detail_route(methods=['get'], suffix='Shouts')
    def shouts(self, request, *args, **kwargs):
        """
        Get tag shouts

        [Shouts Pagination](https://docs.google.com/document/d/1Zp9Ks3OwBQbgaDRqaULfMDHB-eg9as6_wHyvrAWa8u0/edit#heading=h.97r3lxfv95pj)
        ---
        serializer: ShoutSerializer
        omit_parameters:
            - form
        parameters:
            - name: shout_type
              paramType: query
              defaultValue: all
              enum:
                - request
                - offer
                - all
            - name: before
              description: timestamp to get shouts before
              paramType: query
            - name: after
              description: timestamp to get shouts after
              paramType: query
            - name: page_size
              paramType: query
        """
        tag = self.get_object()

        shout_type = request.query_params.get('shout_type', 'all')
        if shout_type not in ['offer', 'request', 'all']:
            raise ValidationError({'shout_type': "should be `offer`, `request` or `all`."})

        # todo: deprecate old method?
        # todo: refactor to use shout index filter
        # temp compatibility for 'before' and 'after'
        before_query_param = request.query_params.get('before')
        after_query_param = request.query_params.get('after')
        if before_query_param or after_query_param:
            self.pagination_class = ReverseDateTimePagination
            shouts = stream_controller.get_stream_shouts_qs(tag.stream, shout_type)
        else:
            self.pagination_class = PageNumberIndexPagination
            self.model = Shout
            self.index_model = ShoutIndex
            self.select_related = ('item', 'category__main_tag', 'item__currency', 'user__profile')
            self.prefetch_related = ('item__videos',)
            self.defer = ()
            shouts = ShoutIndex.search().filter('term', tags=tag.name).sort('-date_published')
            if shout_type != 'all':
                shouts = shouts.query('match', type=shout_type)

        page = self.paginate_queryset(shouts)
        serializer = ShoutSerializer(page, many=True, context={'request': request})
        return self.get_paginated_response(serializer.data)
