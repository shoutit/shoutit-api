# -*- coding: utf-8 -*-
"""

"""
from rest_framework import permissions, viewsets, filters, status, mixins
from rest_framework.decorators import detail_route, list_route
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework_extensions.mixins import DetailSerializerMixin

from shoutit.api.v2.views.shout_views import ShoutViewSet
from shoutit.controllers import listen_controller
from shoutit.models import ShoutIndex, Tag
from . import DEFAULT_PARSER_CLASSES_v2
from ..filters import TagFilter
from ..pagination import (ShoutitPageNumberPagination, PageNumberIndexPagination)
from ..serializers import (TagSerializer, TagDetailSerializer, FeaturedTagSerializer, UserSerializer, ShoutSerializer)


class TagViewSet(DetailSerializerMixin, mixins.ListModelMixin, viewsets.GenericViewSet):
    """
    Tag API Resource.
    """
    lookup_field = 'name'
    parser_classes = DEFAULT_PARSER_CLASSES_v2
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

    @list_route(methods=['post', 'delete'], suffix='Batch listen')
    def batch_listen(self, request, *args, **kwargs):
        """
        Start/Stop listening to a multiple Tags
        ###REQUIRES AUTH
        ###Listen
        <pre><code>
        POST: /v2/tags/listen
        </code></pre>
        <pre><code>
        {
          "tags": [
            {
              "name": "2002-honda-cbr-954rr"
            },
            {
              "name": "paradox"
            },
            {
              "name": "shanghai"
            }
          ]
        }
        </code></pre>

        ###Stop listening
        <pre><code>
        DELETE: /v2/tags/listen
        </code></pre>
        <pre><code>
        {
          "tags": [
            {
              "name": "2002-honda-cbr-954rr"
            },
            {
              "name": "paradox"
            },
            {
              "name": "shanghai"
            }
          ]
        }
        </code></pre>
        ---
        omit_serializer: true
        omit_parameters:
            - form
            - query
        parameters:
            - name: body
              paramType: body
        """
        tag_dicts = request.data.get('tags', [])
        TagSerializer(data=tag_dicts, many=True).is_valid(raise_exception=True)
        tag_names = [str(t['name']) for t in tag_dicts]
        tags = Tag.objects.filter(name__in=tag_names)
        api_client = getattr(request, 'api_client', None)

        if request.method == 'POST':
            listen_controller.listen_to_objects(request.user, tags, api_client=api_client, api_version=request.version)
            msg = "you started listening to {} shouts".format(tag_names)
        else:
            listen_controller.stop_listening_to_objects(request.user, tags)
            msg = "you stopped listening to {} shouts".format(tag_names)

        ret = {
            'data': {'success': msg},
            'status': status.HTTP_201_CREATED if request.method == 'POST' else status.HTTP_202_ACCEPTED
        }
        return Response(**ret)

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
        api_client = getattr(request, 'api_client', None)

        if request.method == 'POST':
            listen_controller.listen_to_object(request.user, tag, api_client=api_client, api_version=request.version)
            msg = "you started listening to {} shouts".format(tag.name)
        else:
            listen_controller.stop_listening_to_object(request.user, tag)
            msg = "you stopped listening to {} shouts".format(tag.name)

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
            raise ValidationError({'shout_type': "should be `offer`, `request` or `all`"})

        self.pagination_class = PageNumberIndexPagination
        setattr(self, 'get_queryset', ShoutViewSet().get_queryset)
        shouts = ShoutIndex.search().filter('term', tags=tag.name).sort('-published_at')
        if shout_type != 'all':
            shouts = shouts.query('match', type=shout_type)

        page = self.paginate_queryset(shouts)
        serializer = ShoutSerializer(page, many=True, context={'request': request})
        return self.get_paginated_response(serializer.data)

    @detail_route(methods=['get'], suffix='Related tags')
    def related(self, request, *args, **kwargs):
        """
        List related tags to this tag
        ---
        serializer: TagSerializer
        omit_parameters:
            - form
        parameters:
            - name: page
              paramType: query
            - name: page_size
              paramType: query
        """
        tag = self.get_object()
        tags = Tag.objects.filter(category__in=tag.category.values_list('id', flat=True))
        page = self.paginate_queryset(tags)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)
