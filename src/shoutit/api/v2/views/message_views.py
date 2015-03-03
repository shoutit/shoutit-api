# -*- coding: utf-8 -*-
"""

"""
from __future__ import unicode_literals

from rest_framework import permissions, viewsets, filters, mixins, status
from rest_framework.response import Response
from rest_framework.decorators import detail_route
from rest_framework.settings import api_settings
from rest_framework_extensions.mixins import DetailSerializerMixin

from shoutit.api.v2.mixins import CustomPaginationSerializerMixin
from shoutit.api.v2.serializers import ConversationSerializer, MessageSerializer, ConversationDetailSerializer, MessageDetailSerializer

from shoutit.controllers import message_controller

from shoutit.models import Message2, Conversation2
from shoutit.api.v2.permissions import IsContributor, IsOwnerOrReadOnly, IsOwnerOrContributorsReadOnly


class ConversationViewSet(DetailSerializerMixin, CustomPaginationSerializerMixin, mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    """
    Conversation API Resource.
    """
    lookup_field = 'id'
    lookup_value_regex = '[0-9a-f-]{32,36}'

    serializer_class = ConversationSerializer
    serializer_detail_class = ConversationDetailSerializer

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

    def retrieve(self, request, *args, **kwargs):
        """
        Get conversation
        ---
        serializer: ConversationDetailSerializer
        omit_parameters:
            - form
        """
        return super(ConversationViewSet, self).retrieve(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        """
        Delete conversation
        ```
        NOT IMPLEMENTED
        ```
        ---
        omit_serializer: true
        omit_parameters:
            - form
        """
        # conversation = self.get_object()
        # message_controller.hide_conversation2_from_user(conversation, request.user)
        # return Response(status.HTTP_204_NO_CONTENT)
        return Response()

    @detail_route(methods=['get'])
    def messages(self, request, *args, **kwargs):
        """
        Get conversation messages
        ---
        serializer: MessageDetailSerializer
        parameters:
            - name: search
              description: NOT ACTIVE
              paramType: query
        """
        conversation = self.get_object()
        instance = conversation.get_messages_qs()
        page = self.paginate_queryset(instance)
        serializer = self.get_custom_pagination_serializer(page, MessageDetailSerializer)
        return Response(serializer.data)

    @detail_route(methods=['post'])
    def reply(self, request, *args, **kwargs):
        """
        Reply in a conversation

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

    @detail_route(methods=['post', 'delete'])
    def read(self, request, *args, **kwargs):
        """
        Read/unread message
        ---
        omit_serializer: true
        omit_parameters:
            - form
        """
        message = self.get_object()
        if request.method == 'POST':
            message_controller.mark_message2_as_read(message, request.user)
            return Response(status.HTTP_201_CREATED)

        else:
            message_controller.mark_message2_as_unread(message, request.user)
            return Response(status.HTTP_204_NO_CONTENT)

