# -*- coding: utf-8 -*-
"""

"""
from __future__ import unicode_literals

from rest_framework import permissions, viewsets, filters, mixins, status
from rest_framework.response import Response
from rest_framework.decorators import detail_route

from shoutit.api.v2.pagination import DateTimePagination, ReverseModifiedDateTimePagination
from shoutit.api.v2.serializers import ConversationSerializer, MessageSerializer, MessageDetailSerializer

from shoutit.controllers import message_controller

from shoutit.models import Message2
from shoutit.api.v2.permissions import IsContributor


class ConversationViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    """
    Conversation API Resource.
    """
    lookup_field = 'id'
    lookup_value_regex = '[0-9a-f-]{32,36}'

    serializer_class = ConversationSerializer

    pagination_class = ReverseModifiedDateTimePagination

    # todo: conversations search
    # filter_backends = (filters.DjangoFilterBackend, filters.SearchFilter)
    # filter_fields = ('id',)
    # search_fields = ('id',)

    permission_classes = (permissions.IsAuthenticated, IsContributor)

    def get_queryset(self):
        return self.request.user.conversations2.all().order_by('-modified_at')

    def list(self, request, *args, **kwargs):
        """
        Get signed in user conversations

        ###Response
        <pre><code>
        {
          "count": 3, // number of results
          "next": null, // next results page url
          "previous": null, // previous results page url
          "results": [] // list of `ConversationSerializer`
        }
        </code></pre>
        ---
        serializer: ConversationSerializer
        parameters:
            - name: search
              description: not yet active
              paramType: query
        """
        return super(ConversationViewSet, self).list(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        """
        Delete conversation
        ---
        omit_serializer: true
        omit_parameters:
            - form
        """
        conversation = self.get_object()
        conversation.mark_as_deleted(request.user)
        return Response(status.HTTP_204_NO_CONTENT)

    @detail_route(methods=['get'], suffix='Messages')
    def messages(self, request, *args, **kwargs):
        """
        Get conversation messages

        Using `before` and `after` query params together is not allowed.

        First call returns the most recent messages in the following order:

        * message 4
        * message 5
        * message 6 (most recent message)

        ###Previous messages
        set `before` to the timestamp of the first message in the current page eg.

        <pre><code>GET /api/v2/conversations/{conversation_id}/messages?before={message4_timestamp}
        </code></pre>

        ###Later messages
        set `after` to the timestamp of the last message in the current page

        <pre><code>GET /api/v2/conversations/{conversation_id}/messages?after={message6_timestamp}
        </code></pre>

        > `next` and `previous` attributes contain the correct url to be used for next and previous pages based. They can be either used directly or parsed to extract query params and construct required url.

        > Note that if `page_size` is specified in a request, it should be also specified with same value for next and previous requests, to return correct results.

        ---
        serializer: MessageDetailSerializer
        parameters:
            - name: before
              description: timestamp to get messages before
              paramType: query
            - name: after
              description: timestamp to get messages after
              paramType: query
        """
        conversation = self.get_object()
        messages_qs = conversation.get_messages_qs2()
        self.pagination_class = DateTimePagination
        page = self.paginate_queryset(messages_qs)

        # only keep the messages that were not deleted by this user
        messages_ids = [message.id for message in page.object_list]
        deleted_messages_ids = request.user.deleted_messages2.filter(id__in=messages_ids).values_list('id', flat=True)
        [page.object_list.remove(message) for message in page.object_list if message.id in deleted_messages_ids]

        serializer = MessageDetailSerializer(page, many=True)
        conversation.mark_as_read(request.user)
        return self.get_paginated_response(serializer.data)

    @detail_route(methods=['post', 'delete'], suffix='Read')
    def read(self, request, *args, **kwargs):
        """
        Mark Conversation as read/unread

        Marking as read will mark `all` messages as read

        Marking as unread will mark only `last_message` as unread
        ---
        omit_serializer: true
        omit_parameters:
            - form
        """
        conversation = self.get_object()
        if request.method == 'POST':
            conversation.mark_as_read(request.user)
            return Response(status.HTTP_201_CREATED)

        elif request.method == 'DELETE':
            conversation.mark_as_unread(request.user)
            return Response(status.HTTP_204_NO_CONTENT)

    @detail_route(methods=['post'], suffix='Reply')
    def reply(self, request, *args, **kwargs):
        """
        Reply in conversation

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
        response_serializer: MessageDetailSerializer
        omit_parameters:
            - form
        parameters:
            - name: body
              paramType: body
        """
        conversation = self.get_object()
        serializer = MessageDetailSerializer(data=request.data, partial=True, context={'request': request})
        serializer.is_valid(raise_exception=True)
        text = serializer.validated_data['text']
        attachments = serializer.validated_data['attachments']
        message = message_controller.send_message2(conversation, request.user, text=text, attachments=attachments)
        message = MessageDetailSerializer(instance=message, context={'request': request})
        headers = self.get_success_message_headers(message.data)
        return Response(message.data, status=status.HTTP_201_CREATED, headers=headers)

    def get_success_message_headers(self, data):
        return {'Location': data['conversation_url']}


class MessageViewSet(mixins.DestroyModelMixin, viewsets.GenericViewSet):
    """
    API endpoint that allows conversations/messages to be viewed or added.
    """
    lookup_field = 'id'
    lookup_value_regex = '[0-9a-f-]{32,36}'

    serializer_class = MessageSerializer

    filter_backends = (filters.DjangoFilterBackend, filters.SearchFilter)
    filter_fields = ('id',)
    search_fields = ('id',)

    permission_classes = (permissions.IsAuthenticated, IsContributor)

    def get_queryset(self):
        return Message2.objects.all()

    def destroy(self, request, *args, **kwargs):
        """
        Delete message
        ---
        omit_serializer: true
        omit_parameters:
            - form
        """
        message = self.get_object()
        message_controller.hide_message2_from_user(message, request.user)
        return Response(status.HTTP_204_NO_CONTENT)
