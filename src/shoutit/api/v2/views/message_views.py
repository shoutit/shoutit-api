# -*- coding: utf-8 -*-
"""

"""
from __future__ import unicode_literals

from rest_framework import permissions, viewsets, filters, mixins, status
from rest_framework.response import Response
from rest_framework.decorators import detail_route
from rest_framework.settings import api_settings

from shoutit.api.v2.mixins import CustomPaginationSerializerMixin
from shoutit.api.v2.serializers import ConversationSerializer, MessageSerializer

from shoutit.controllers import message_controller

from shoutit.models import Message2, Conversation2
from shoutit.api.v2.permissions import IsContributor, IsOwnerOrReadOnly, IsOwnerOrContributorsReadOnly


class ConversationViewSet(CustomPaginationSerializerMixin, mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    """
    Conversation API Resource.
    """
    lookup_field = 'id'
    lookup_value_regex = '[0-9a-f-]{32,36}'

    serializer_class = ConversationSerializer

    # todo: conversations search
    # filter_backends = (filters.DjangoFilterBackend, filters.SearchFilter)
    # filter_fields = ('id',)
    # search_fields = ('id',)

    permission_classes = (permissions.IsAuthenticated, IsContributor)

    def get_queryset(self):
        return Conversation2.objects.filter(users=self.request.user)

    def list(self, request, *args, **kwargs):
        """
        Get signed in user conversations

        ###Conversation Object
        <pre><code>
        {
          "id": "358ab248-8128-465b-971e-80d8c95f0270",
          "api_url": "http://shoutit.dev:8000/api/v2/conversations/358ab248-8128-465b-971e-80d8c95f0270",
          "web_url": "",
          "type": "about_shout", // currently could be either 'chat' or 'about_shout'
          "users": [], // list of {User Object}
          "last_message": {} // last {Message Object},
          "shout": {} // {Shout Object} only set if the conversation of type 'about_shout'
        }
        </code></pre>

        ###Response
        <pre><code>
        {
          "count": 3, // number of results
          "next": null, // next results page url
          "previous": null, // previous results page url
          "results": [] // list of {Conversation Object} as described above
        }
        </code></pre>
        ---
        omit_serializer: true
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
        omit_serializer: true
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
        return Response()

    @detail_route(methods=['get'])
    def messages(self, request, *args, **kwargs):
        """
        Get conversation messages

        ###Response {Message Object}
        <pre><code>
        {
          "id": "d75e8536-473a-4209-9147-8c93ab0c2b75",
          "read_url": "",
          "delete_url": "",
          "user": {}, // {User Object}
          "message": "hey!",
          "attachments": [] // list of {Attachment Object}
        }
        </code></pre>

        ####{Attachment Object}
        <pre><code>
        {
          "{attachment type}": {attachment}
        }
        </code></pre>

        attachment type: 'shout' or 'location'

        attachment: {Shout Object} or {Shared Location Object}

        ####{Shared Location Object}
        <pre><code>
        {
          "latitude": 12.3456,
          "longitude": 12.3456
        }
        </code></pre>
        ---
        omit_serializer: true
        parameters:
            - name: search
              description: NOT ACTIVE
              paramType: query
        """
        conversation = self.get_object()
        instance = conversation.get_messages_qs()
        page = self.paginate_queryset(instance)
        serializer = self.get_custom_pagination_serializer(page, MessageSerializer)
        return Response(serializer.data)

    @detail_route(methods=['post'])
    def reply(self, request, *args, **kwargs):
        """
        Reply in a conversation

        ###Request
        <pre><code>
        {
            "messag": "text goes here",
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
        omit_serializer: true
        omit_parameters:
            - form
        parameters:
            - name: body
              paramType: body
        """
        conversation = self.get_object()
        serializer = MessageSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        text = serializer.validated_data['message']
        attachments = serializer.validated_data['attachments']
        message = message_controller.send_message2(conversation, request.user, text=text, attachments=attachments)
        message = MessageSerializer(instance=message)
        headers = self.get_success_headers(message.data)
        return Response(message.data, status=status.HTTP_201_CREATED, headers=headers)

    def get_success_headers(self, data):
        try:
            return {'Location': data[api_settings.URL_FIELD_NAME]}
        except (TypeError, KeyError):
            return {}


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

        ```
        NOT IMPLEMENTED
        ```

        ---
        omit_serializer: true
        omit_parameters:
            - form
        """
        return Response()

    @detail_route(methods=['post', 'delete'])
    def read(self, request, *args, **kwargs):
        """
        Read/unread message

        ```
        NOT IMPLEMENTED
        ```

        ---
        omit_serializer: true
        omit_parameters:
            - form
        """
        return Response()
