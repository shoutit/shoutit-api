# -*- coding: utf-8 -*-
"""

"""
from __future__ import unicode_literals

from rest_framework import permissions, status
from rest_framework.decorators import detail_route
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework_extensions.mixins import DetailSerializerMixin

from shoutit.api.v2.filters import ShoutIndexFilterBackend
from shoutit.api.v2.pagination import PageNumberIndexPagination
from shoutit.api.v2.permissions import IsOwnerModify
from shoutit.api.v2.serializers import ShoutSerializer, ShoutDetailSerializer, MessageSerializer
from shoutit.api.v2.views.viewsets import NoUpdateModelViewSet, UUIDViewSetMixin
from shoutit.controllers import shout_controller
from shoutit.models import Shout
from shoutit.models.post import ShoutIndex


class ShoutViewSet(DetailSerializerMixin, UUIDViewSetMixin, NoUpdateModelViewSet):
    """
    Shout API Resource
    """
    serializer_class = ShoutSerializer
    serializer_detail_class = ShoutDetailSerializer

    filter_backends = (ShoutIndexFilterBackend,)
    model = Shout
    filters = {'is_disabled': False}
    select_related = ('item', 'category__main_tag', 'item__currency', 'user__profile')
    prefetch_related = ('item__videos',)
    defer = ()
    pagination_class = PageNumberIndexPagination

    permission_classes = (permissions.IsAuthenticatedOrReadOnly, IsOwnerModify)

    def get_queryset(self):
        return (Shout.objects.get_valid_shouts(get_expired=True).all()
                .select_related(*self.select_related)
                .prefetch_related(*self.prefetch_related)
                .defer(*self.defer))

    def filter_queryset(self, queryset, *args, **kwargs):
        """
        Given a queryset, filter it with whichever filter backend is in use.

        You are unlikely to want to override this method, although you may need
        to call it either from a list view, or from a custom `get_object`
        method if you want to apply the configured filtering backend to the
        default queryset.
        """
        for backend in list(self.filter_backends):
            queryset = backend().filter_queryset(self.request, queryset, self, *args, **kwargs)
        return queryset

    def get_index_search(self):
        return ShoutIndex.search()

    def list(self, request, *args, **kwargs):
        """
        Get shouts

        [Shouts Pagination](https://docs.google.com/document/d/1Zp9Ks3OwBQbgaDRqaULfMDHB-eg9as6_wHyvrAWa8u0/edit#heading=h.97r3lxfv95pj)
        ---
        serializer: ShoutSerializer
        parameters:
            - name: search
              description: space or comma separated keywords to search in title, text, tags
              paramType: query
            - name: shout_type
              paramType: query
              defaultValue: all
              enum:
                - request
                - offer
                - all
            - name: country
              paramType: query
            - name: city
              paramType: query
            - name: min_price
              type: float
              paramType: query
              type: float
            - name: max_price
              paramType: query
            - name: down_left_lat
              description: -90 to 90, can not be greater than up_right_lat
              type: float
              paramType: query
            - name: down_left_lng
              description: -180 to 180, can not be greater than up_right_lng
              type: float
              paramType: query
            - name: up_right_lat
              description: -90 to 90
              type: float
              paramType: query
            - name: up_right_lng
              description: -180 to 180
              type: float
              paramType: query
            - name: category
              description: the category name
              paramType: query
            - name: tags
              description: space or comma separated tags. returned shouts will contain ALL of them
              paramType: query
            - name: discover
              description: discover item id to list its shouts
              paramType: query
        """
        shouts = self.filter_queryset(self.get_index_search())
        page = self.paginate_queryset(shouts)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)

    def create(self, request, *args, **kwargs):
        """
        Create shout

        ###Request
        <pre><code>
        {
          "type": "offer", // `offer` or `request`
          "title": "macbook pro 15",
          "text": "apple macbook pro 15-inch in good condition for sale.", // 10 to 1000 chars
          "price": 1000,
          "currency": "EUR",
          "images": [], // list of image urls
          "videos": [], // list of {Video Object}s
          "category": {"name": "Computers & Networking"},
          "tags": [{"name":"macbook-pro"}, {"name":"apple"}, {"name":"used"}],
          "location": {
            "latitude": 25.1593957,
            "longitude": 55.2338326,
            "address": "Whatever Street 31",
          }
        }
        </code></pre>
        ---
        serializer: ShoutDetailSerializer
        omit_parameters:
            - form
        parameters:
            - name: body
              paramType: body
        """
        serializer = ShoutDetailSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def retrieve(self, request, *args, **kwargs):
        """
        Get shout

        ---
        serializer: ShoutDetailSerializer
        """
        return super(ShoutViewSet, self).retrieve(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        """
        Modify shout

        <pre><code>
        {
          "title": "macbook pro 15",
          "text": "apple macbook pro 15-inch in good condition for sale.", // 10 to 1000 chars
          "price": 1000,
          "currency": "EUR",
          "images": [], // list of image urls
          "videos": [], // list of {Video Object}s
          "category": {"name": "Computers & Networking"},
          "tags": [{"name":"macbook-pro"}, {"name":"apple"}, {"name":"used"}],
          "location": {
            "latitude": 25.1593957,
            "longitude": 55.2338326,
            "address": "Whatever Street 31",
          }
        }
        </code></pre>
        ---
        serializer: ShoutDetailSerializer
        omit_parameters:
            - form
        parameters:
            - name: body
              paramType: body
        """
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        """
        Delete shout

        ---
        omit_serializer: true
        omit_parameters:
            - form
        """
        return super(ShoutViewSet, self).destroy(request, *args, **kwargs)

    def perform_destroy(self, instance):
        shout_controller.delete_post(instance)

    @detail_route(methods=['post'], suffix='Reply')
    def reply(self, request, *args, **kwargs):
        """
        Reply to shout

        ###Request
        <pre><code>
        {
            "text": "text goes here",
            "attachments": [
                {
                    "shout": {
                        "id": ""
                    }
                },
                {
                    "location": {
                        "latitude": 12.345,
                        "longitude": 12.345
                    }
                },
                {
                    "images": [], // list of image urls
                    "videos": [], // list of {Video Object}s
                }
            ]
        }
        </code></pre>

        ---
        serializer: MessageSerializer
        omit_parameters:
            - form
        parameters:
            - name: body
              paramType: body
        """
        # Todo: move validation to the serializer
        shout = self.get_object()
        if request.user == shout.owner:
            raise ValidationError({'error': "You can not start a conversation about your own shout"})
        context = {
            'request': request,
            'conversation': None,
            'to_users': [shout.owner],
            'about': shout
        }
        serializer = MessageSerializer(data=request.data, partial=True, context=context)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        headers = self.get_success_message_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def get_success_message_headers(self, data):
        loc = reverse('conversation-messages', kwargs={'id': data['conversation_id']}, request=self.request)
        return {'Location': loc}

    @detail_route(methods=['get'], suffix='Related shouts')
    def related(self, request, *args, **kwargs):
        """
        Related shouts

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
            - name: page
              paramType: query
            - name: page_size
              paramType: query
        """
        shout = self.get_object()
        extra_query_params = {
            'search': "%s %s" % (shout.item.name, " ".join(shout.tags)),
            'country': shout.country,
            'shout_type': shout.get_type_display(),
            'category': shout.category.name,
            'exclude_ids': [shout.pk]
        }
        shouts = self.filter_queryset(self.get_index_search(), extra_query_params=extra_query_params)
        page = self.paginate_queryset(shouts)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)
