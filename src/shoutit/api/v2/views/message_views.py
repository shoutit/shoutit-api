# -*- coding: utf-8 -*-
"""

"""
from __future__ import unicode_literals

from rest_framework import permissions, viewsets, mixins, status
from rest_framework.response import Response
from rest_framework.decorators import detail_route
from rest_framework.reverse import reverse

from shoutit.api.v2.pagination import DateTimePagination, ReverseModifiedDateTimePagination
from shoutit.api.v2.serializers import ConversationSerializer, MessageSerializer
from shoutit.api.v2.views.viewsets import UUIDViewSetMixin

from shoutit.controllers import message_controller

from shoutit.models import Message
from shoutit.api.v2.permissions import IsContributor


class ConversationViewSet(UUIDViewSetMixin, mixins.ListModelMixin, viewsets.GenericViewSet):
    """
    Conversation API Resource.
    """
    serializer_class = ConversationSerializer

    pagination_class = ReverseModifiedDateTimePagination

    permission_classes = (permissions.IsAuthenticated, IsContributor)

    # todo: conversations / messages search

    def get_queryset(self):
        return self.request.user.conversations2.all().order_by('-modified_at')

    def list(self, request, *args, **kwargs):
        """
        Get signed in user conversations

        [Conversations Pagination](https://docs.google.com/document/d/1Zp9Ks3OwBQbgaDRqaULfMDHB-eg9as6_wHyvrAWa8u0/edit#heading=h.abebl6lr97rm)
        ---
        serializer: ConversationSerializer
        parameters:
            - name: search
              description: NOT IMPLEMENTED
              paramType: query
            - name: before
              description: timestamp to get messages before
              paramType: query
            - name: after
              description: timestamp to get messages after
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

        [Messages Pagination](https://docs.google.com/document/d/1Zp9Ks3OwBQbgaDRqaULfMDHB-eg9as6_wHyvrAWa8u0/edit#heading=h.xnc089w6znop)
        ---
        serializer: MessageSerializer
        parameters:
            - name: search
              description: NOT IMPLEMENTED
              paramType: query
            - name: before
              description: timestamp to get messages before
              paramType: query
            - name: after
              description: timestamp to get messages after
              paramType: query
            - name: page_size
              paramType: query
        """
        conversation = self.get_object()
        messages_qs = conversation.get_messages_qs2()
        self.pagination_class = DateTimePagination
        page = self.paginate_queryset(messages_qs)

        # only keep the messages that were not deleted by this user
        messages_ids = [message.id for message in page.object_list]
        deleted_messages_ids = request.user.deleted_messages.filter(id__in=messages_ids).values_list('id', flat=True)
        [page.object_list.remove(message) for message in page.object_list if message.id in deleted_messages_ids]

        serializer = MessageSerializer(page, many=True, context={'request': request})
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
        else:
            return Response()

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
        response_serializer: MessageSerializer
        omit_parameters:
            - form
        parameters:
            - name: body
              paramType: body
        """
        conversation = self.get_object()
        serializer = MessageSerializer(data=request.data, partial=True, context={'request': request})
        serializer.is_valid(raise_exception=True)
        text = serializer.validated_data['text']
        attachments = serializer.validated_data['attachments']
        message = message_controller.send_message(conversation, request.user, text=text, attachments=attachments, request=request)
        message = MessageSerializer(instance=message, context={'request': request})
        headers = self.get_success_message_headers(message.data)
        return Response(message.data, status=status.HTTP_201_CREATED, headers=headers)

    def get_success_message_headers(self, data):
        return {'Location': reverse('conversation-messages', kwargs={'id': data['conversation_id']}, request=self.request)}


class MessageViewSet(UUIDViewSetMixin, mixins.DestroyModelMixin, viewsets.GenericViewSet):
    """
    API endpoint that allows conversations/messages to be viewed or added.
    """
    serializer_class = MessageSerializer

    permission_classes = (permissions.IsAuthenticated, IsContributor)

    def get_queryset(self):
        return Message.objects.all()

    def destroy(self, request, *args, **kwargs):
        """
        Delete message
        ---
        omit_serializer: true
        omit_parameters:
            - form
        """
        return super(MessageViewSet, self).destroy(request, *args, **kwargs)

    def perform_destroy(self, message):
        message_controller.hide_message_from_user(message, self.request.user)
