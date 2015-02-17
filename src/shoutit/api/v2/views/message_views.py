# -*- coding: utf-8 -*-
"""

"""
from __future__ import unicode_literals

from rest_framework import permissions, viewsets, filters, mixins
from rest_framework.response import Response
from rest_framework.decorators import detail_route

from shoutit.controllers import message_controller

from shoutit.models import Message, Conversation
from shoutit.api.v2.permissions import IsContributor, IsOwnerOrReadOnly, IsOwnerOrContributorsReadOnly
from shoutit.api.renderers import render_conversation, render_message


class ConversationViewSet(viewsets.GenericViewSet):
    """
    API endpoint that allows conversations to be listed, viewed or deleted.
    """
    lookup_field = 'id'
    lookup_value_regex = '[0-9a-f-]{32,36}'
    # serializer_class = UserSerializer2

    filter_backends = (filters.DjangoFilterBackend, filters.SearchFilter)
    filter_fields = ('id',)
    search_fields = ('id',)

    permission_classes = (permissions.IsAuthenticated, IsContributor)

    def get_queryset(self):
        return Conversation.objects.all()

    def list(self, request, *args, **kwargs):
        """
        get signed in user conversations
        """
        # conversations = self.filter_queryset(self.get_queryset())
        conversations = message_controller.ReadConversations(request.user)
        ret = {
            "results": [render_conversation(conversation) for conversation in conversations]
        }
        return Response(ret)

    def destroy(self, request, *args, **kwargs):
        """
        delete conversation
        """
        return Response()

    @detail_route(methods=['get'])
    def messages(self, request, *args, **kwargs):
        """
        get conversation messages
        """
        return Response()

    @detail_route(methods=['post'])
    def reply(self, request, *args, **kwargs):
        """
        reply in a conversation
        """
        return Response()


class MessageViewSet(mixins.RetrieveModelMixin, mixins.DestroyModelMixin, viewsets.GenericViewSet):
    """
    API endpoint that allows conversations/messages to be viewed or added.
    """
    lookup_field = 'id'
    lookup_value_regex = '[0-9a-f-]{32,36}'
    # serializer_class = UserSerializer2

    filter_backends = (filters.DjangoFilterBackend, filters.SearchFilter)
    filter_fields = ('id',)
    search_fields = ('id',)

    permission_classes = (permissions.IsAuthenticated, IsContributor)

    def get_queryset(self):
        return Message.objects.all()

    def destroy(self, request, *args, **kwargs):
        """
        delete message
        """
        return Response()

    @detail_route(methods=['post', 'delete'])
    def read(self, request, *args, **kwargs):
        """
        read/unread message
        """
        return Response()
