# -*- coding: utf-8 -*-
"""

"""
from __future__ import unicode_literals

from rest_framework import permissions, viewsets, filters, status, mixins
from rest_framework.response import Response
from rest_framework.decorators import detail_route
from rest_framework_extensions.mixins import DetailSerializerMixin

from shoutit.api.v2.filters import TagFilter
from shoutit.api.v2.pagination import (ShoutitPageNumberPagination, PageNumberIndexPagination)
from shoutit.api.v2.serializers import *  # NOQA
from shoutit.controllers import listen_controller
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
        List Tags based on `search` query param.
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
            - name: postal_code
              description: only used when type is `featured` or `top`
              paramType: query
            - name: state
              description: only used when type is `featured` or `top`
              paramType: query
            - name: city
              description: only used when type is `featured` or `top`
              paramType: query
            - name: category
              description: return tags that belong to this category only
              paramType: query
        omit_parameters:
            - form
            - path
        """
        tags_type = request.query_params.get('type')
        if tags_type == 'featured':
            self.serializer_class = FeaturedTagSerializer
        return super(TagViewSet, self).list(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        """
        Get a Tag
        ---
        serializer: TagDetailSerializer
        omit_parameters:
            - form
            - query
        """
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @detail_route(methods=['post', 'delete'], suffix='Listen')
    def listen(self, request, *args, **kwargs):
        """
        Start/Stop listening to a Tag
        ###REQUIRES AUTH
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
            - query
        """
        tag = self.get_object()

        if request.method == 'POST':
            listen_controller.listen_to_object(request.user, tag, request)
            msg = "you started listening to {} shouts.".format(tag.name)
        else:
            listen_controller.stop_listening_to_object(request.user, tag)
            msg = "you stopped listening to {} shouts.".format(tag.name)

        ret = {
            'data': {'success': msg},
            'status': status.HTTP_201_CREATED if request.method == 'POST' else status.HTTP_202_ACCEPTED
        }
        return Response(**ret)

    @detail_route(methods=['get'], suffix='Listeners')
    def listeners(self, request, *args, **kwargs):
        """
        List the Tag listeners
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
        listeners = listen_controller.get_object_listeners(tag)
        page = self.paginate_queryset(listeners)
        serializer = UserSerializer(page, many=True, context={'request': request})
        return self.get_paginated_response(serializer.data)

    @detail_route(methods=['get'], suffix='Shouts')
    def shouts(self, request, *args, **kwargs):
        """
        List the Tag shouts.
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
            - name: page_size
              paramType: query
        """
        tag = self.get_object()

        # todo: refactor to use shout index filter
        shout_type = request.query_params.get('shout_type', 'all')
        if shout_type not in ['offer', 'request', 'all']:
            raise ValidationError({'shout_type': "should be `offer`, `request` or `all`."})

        self.pagination_class = PageNumberIndexPagination
        setattr(self, 'model', Shout)
        setattr(self, 'filters', {'is_disabled': False})
        setattr(self, 'select_related', ('item', 'category__main_tag', 'item__currency', 'user__profile'))
        setattr(self, 'prefetch_related', ('item__videos',))
        setattr(self, 'defer', ())
        shouts = ShoutIndex.search().filter('term', tags=tag.name).sort('-date_published')
        if shout_type != 'all':
            shouts = shouts.query('match', type=shout_type)

        page = self.paginate_queryset(shouts)
        serializer = ShoutSerializer(page, many=True, context={'request': request})
        return self.get_paginated_response(serializer.data)
