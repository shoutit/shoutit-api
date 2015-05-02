# -*- coding: utf-8 -*-
"""

"""
from __future__ import unicode_literals
from collections import OrderedDict

from rest_framework import permissions, status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.decorators import detail_route
from rest_framework.reverse import reverse
from rest_framework_extensions.mixins import DetailSerializerMixin
from shoutit.api.v2.filters import ShoutIndexFilterBackend
from shoutit.api.v2.pagination import ReverseDateTimeIndexPagination, PageNumberIndexPagination
from shoutit.api.v2.serializers import ShoutSerializer, ShoutDetailSerializer, MessageSerializer
from shoutit.api.v2.views.viewsets import NoUpdateModelViewSet, UUIDViewSetMixin
from shoutit.controllers import message_controller

from shoutit.models import Shout
from shoutit.api.v2.permissions import IsOwnerModify
from shoutit.models.post import ShoutIndex
from shoutit.controllers import shout_controller


class ShoutViewSet(DetailSerializerMixin, UUIDViewSetMixin, NoUpdateModelViewSet):
    """
    Shout API Resource
    """
    serializer_class = ShoutSerializer
    serializer_detail_class = ShoutDetailSerializer

    pagination_class = PageNumberIndexPagination

    filter_backends = (ShoutIndexFilterBackend,)
    model = Shout
    index_model = ShoutIndex
    select_related = ('item', 'category__main_tag', 'item__currency', 'user__profile')
    prefetch_related = ('item__videos',)
    defer = ()

    permission_classes = (permissions.IsAuthenticatedOrReadOnly, IsOwnerModify)

    def get_queryset(self):
        return Shout.objects.get_valid_shouts().all()\
            .select_related(*self.select_related)\
            .prefetch_related(*self.prefetch_related)\
            .defer(*self.defer)

    def get_index_search(self):
        return ShoutIndex.search()

    def list(self, request, *args, **kwargs):
        """
        Get shouts

        [Shouts Pagination](https://docs.google.com/document/d/1Zp9Ks3OwBQbgaDRqaULfMDHB-eg9as6_wHyvrAWa8u0/edit#heading=h.97r3lxfv95pj)
        ---
        serializer: ShoutSerializer
        parameters:
            - name: before
              description: timestamp to get shouts before
              paramType: query
            - name: after
              description: timestamp to get shouts after
              paramType: query
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

        # temp compatibility for 'before' and 'after'
        before_query_param = request.query_params.get('before')
        after_query_param = request.query_params.get('after')
        if before_query_param or after_query_param:
            self.pagination_class = ReverseDateTimeIndexPagination

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
          "text": "apple macbook pro 15-inch in good condition for sale.",
          "price": 1000,
          "currency": "EUR",
          "images": [], // image urls
          "videos": [], // {Video Object}
          "category": {"name": "Computers & Networking"}
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

        ```
        NOT IMPLEMENTED!
        ```
        ---
        serializer: ShoutDetailSerializer
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
        shout = self.get_object()
        if request.user == shout.owner:
            raise ValidationError({'error': "You can not start a conversation about your own shout"})
        serializer = MessageSerializer(data=request.data, partial=True, context={'request': request})
        serializer.is_valid(raise_exception=True)
        text = serializer.validated_data['text']
        attachments = serializer.validated_data['attachments']
        message = message_controller.send_message(
            conversation=None, user=request.user, to_users=[shout.owner], about=shout, text=text,
            attachments=attachments, request=request)
        message = MessageSerializer(instance=message, context={'request': request})
        headers = self.get_success_message_headers(message.data)
        return Response(message.data, status=status.HTTP_201_CREATED, headers=headers)

    def get_success_message_headers(self, data):
        return {
            'Location': reverse('conversation-messages', kwargs={'id': data['conversation_id']},
                                request=self.request)
        }
