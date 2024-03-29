# -*- coding: utf-8 -*-
"""

"""
from django.utils.translation import ugettext_lazy as _
from rest_framework import permissions, viewsets, mixins, status
from rest_framework.decorators import detail_route
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework_extensions.mixins import DetailSerializerMixin

from common.constants import CONVERSATION_TYPE_PUBLIC_CHAT
from shoutit.api.permissions import CanContribute, IsAdminOrCanContribute
from shoutit.controllers import message_controller
from shoutit.models import Message, User, Conversation
from ..pagination import DateTimePagination, ReverseModifiedDateTimePagination, ShoutitPageNumberPagination
from ..serializers import (ConversationDetailSerializer,
                           MessageSerializer, BlockProfileSerializer, PromoteAdminSerializer,
                           RemoveProfileSerializer, AddProfileSerializer, UnblockProfileSerializer, ProfileSerializer,
                           MessageAttachmentSerializer, ShoutSerializer, ConversationSerializer)
from ..views.viewsets import UUIDViewSetMixin


def serializer_compat(view_set):
    # Use ConversationSerializer for web and newer mobile clients
    request = view_set.request
    from_web = request.agent == 'web'
    ios_condition = (
        (request.agent == 'ios' and request.app_version is None and request.build_no >= 1378) or
        (request.agent == 'ios' and request.app_version is not None)
    )
    android_condition = request.agent == 'android' and request.build_no >= 1474
    if any([from_web, ios_condition, android_condition]):
        view_set.serializer_class = ConversationSerializer


class ConversationViewSet(DetailSerializerMixin, UUIDViewSetMixin, mixins.ListModelMixin, mixins.RetrieveModelMixin,
                          mixins.CreateModelMixin, viewsets.GenericViewSet):
    """
    Conversation API Resource.
    """
    serializer_class = ConversationDetailSerializer
    serializer_detail_class = ConversationDetailSerializer
    pagination_class = ReverseModifiedDateTimePagination
    permission_classes = (permissions.IsAuthenticated, IsAdminOrCanContribute)

    # todo: conversations / messages search

    def get_queryset(self, *args, **kwargs):
        serializer_compat(self)

        user = self.request.user
        exclude = {'blocked__contains': [user.id]}

        if self._is_request_to_detail_endpoint():
            related = ['creator', 'last_message__user__profile']
            related2 = ['last_message__attachments']
            return Conversation.objects.all().exclude(**exclude).select_related(*related).prefetch_related(*related2)
        else:
            conversation_type = self.request.query_params.get('type')
            if conversation_type == 'public_chat':
                conversations = Conversation.objects
                filters = {
                    'type': CONVERSATION_TYPE_PUBLIC_CHAT,
                    'country': self.request.user.location['country']
                }
            else:
                conversations = user.conversations
                filters = {}

            related = ['last_message__user__profile']
            related2 = ['creator', 'last_message__attachments']
            order = '-modified_at'
            return conversations.filter(**filters).exclude(**exclude).select_related(*related).prefetch_related(
                *related2).order_by(order)
            # return conversations.filter(**filters).exclude(**exclude).select_related(*related).order_by(order)

    def _is_request_to_detail_endpoint(self):
        # Todo (mo): Check why this is overridden
        lookup = self.lookup_url_kwarg or self.lookup_field
        return lookup and lookup in self.kwargs

    def list(self, request, *args, **kwargs):
        """
        List profile conversations.
        ###REQUIRES AUTH
        [Conversations Pagination](https://github.com/shoutit/shoutit-api/wiki/Messaging-Pagination#conversations-pagination)
        ---
        serializer: ConversationDetailSerializer
        parameters:
            - name: search
              description: NOT IMPLEMENTED
              paramType: query
            - name: type
              paramType: query
            - name: before
              description: timestamp to get conversations before
              paramType: query
            - name: after
              description: timestamp to get conversations after
              paramType: query
        """
        return super(ConversationViewSet, self).list(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        """
        Retrieve a Conversation
        ###Example Response
        <pre><code>
        {
          "id": "73e43221-1f65-42c3-8c3e-82325a3e23ff",
          "created_at": 1458658338,
          "modified_at": 1458742115,
          "web_url": "https://api.shoutit.com/conversation/73e43221-1f65-42c3-8c3e-82325a3e23ff",
          "type": "chat",
          "messages_count": 3,
          "unread_messages_count": 0,
          "subject": "",
          "icon": "",
          "admins": [
            "9fc0be8e-a92f-4113-975d-148def4fb2e4"
          ],
          "profiles": "[List of Profile Objects]",
          "last_message": "{Message Object}",
          "about": null,
          "messages_url": "https://api.shoutit.com/v3/conversations/73e43221-1f65-42c3-8c3e-82325a3e23ff/messages",
          "reply_url": "https://api.shoutit.com/v3/conversations/73e43221-1f65-42c3-8c3e-82325a3e23ff/reply"
        }
        </code></pre>
        ---
        serializer: ConversationDetailSerializer
        """
        return super(ConversationViewSet, self).retrieve(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        """
        Create Public Chat conversation in profile's country.
        ###REQUIRES AUTH
        ####Body
        <pre><code>
        {
            "type": "public_chat",
            "subject": "text goes here",
            "icon": "icon url"
        }
        </code></pre>
        ---
        serializer: ConversationDetailSerializer
        omit_parameters:
            - form
        parameters:
            - name: body
              paramType: body
        """
        self.serializer_class = ConversationDetailSerializer
        return super(ConversationViewSet, self).create(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        """
        Update conversation
        ###REQUIRES AUTH
        The logged in profile should be admin in the conversation
        ###Request
        ####Body
        <pre><code>
        {
            "subject": "text goes here",
            "icon": "icon url"
        }
        </code></pre>
        ---
        serializer: ConversationDetailSerializer
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
        Delete a conversation
        ###REQUIRES AUTH
        ---
        omit_serializer: true
        omit_parameters:
            - form
        """
        conversation = self.get_object()
        conversation.mark_as_deleted(request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @detail_route(methods=['get'], suffix='Messages')
    def messages(self, request, *args, **kwargs):
        """
        List the conversation messages
        This will mark the conversation as read regardless of how many unread messages there are.
        ###REQUIRES AUTH
        [Messages Pagination](https://github.com/shoutit/shoutit-api/wiki/Messaging-Pagination#messages-pagination)
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
        related = ['user__profile']
        related2 = ['attachments']
        messages_qs = conversation.messages.all().select_related(*related).prefetch_related(*related2)
        self.pagination_class = DateTimePagination
        page = self.paginate_queryset(messages_qs)

        # Only keep the messages that were not deleted by this user
        messages_ids = [m.id for m in page.object_list]
        deleted_messages_ids = request.user.deleted_messages.filter(id__in=messages_ids).values_list('id', flat=True)
        for message in page.object_list:
            if message.id in deleted_messages_ids:
                page.object_list.remove(message)

        serializer = MessageSerializer(page, many=True, context={'request': request})
        conversation.mark_as_read(request.user)
        return self.get_paginated_response(serializer.data)

    @detail_route(methods=['get'], suffix='Media')
    def media(self, request, *args, **kwargs):
        """
        List the conversation attached media
        ###REQUIRES AUTH
        ###Response
        <pre><code>
        {
          "next": null, // next results page url
          "previous": null, // previous results page url
          "results": [] // list of {MessageAttachmentSerializer} of type `media`
        }
        </code></pre>

        ###MessageAttachmentSerializer of type `media`
        <pre><code>
        {
            "type": "media",
            "images": [
                "https://shout-image.static.shoutit.com/image1.jpg",
                "https://shout-image.static.shoutit.com/image2.jpg"
            ],
            "videos": [
                {
                    "url": "https://shout-image.static.shoutit.com/video.mp4",
                    "thumbnail_url": "https://shout-image.static.shoutit.com/thumbnail.jpg",
                    "provider": "shoutit_s3",
                    "id_on_provider": "38CB868F-B0C8-4B41-AF5A-F57C9FC666C7-1447616915",
                    "duration": 12
                }
            ]
        }
        </code></pre>
        ---
        omit_serializer: true
        parameters:
            - name: page
              paramType: query
            - name: page_size
              paramType: query
        """
        conversation = self.get_object()
        media_attachments = conversation.media_attachments
        self.pagination_class = ShoutitPageNumberPagination
        page = self.paginate_queryset(media_attachments)
        # Todo: Only keep the message attachments that were not deleted by this user
        serializer = MessageAttachmentSerializer(page, many=True, context={'request': request})
        return self.get_paginated_response(serializer.data)

    @detail_route(methods=['get'], suffix='Shouts')
    def shouts(self, request, *args, **kwargs):
        """
        List the conversation attached shouts
        ###REQUIRES AUTH
        ###Response
        <pre><code>
        {
          "next": null, // next results page url
          "previous": null, // previous results page url
          "results": [] // list of {ShoutSerializer}
        }
        </code></pre>
        ---
        omit_serializer: true
        parameters:
            - name: page
              paramType: query
            - name: page_size
              paramType: query
        """
        conversation = self.get_object()
        shout_attachments = conversation.shout_attachments
        self.pagination_class = ShoutitPageNumberPagination
        page = self.paginate_queryset(shout_attachments)
        # Todo: Only keep the message attachments that were not deleted by this user
        serializer = ShoutSerializer(page, many=True, context={'request': request})
        return self.get_paginated_response(serializer.data)

    @detail_route(methods=['post'], suffix='Delete Messages')
    def delete_messages(self, request, *args, **kwargs):
        """
        <pre><code>
        POST: /conversations/{conversation_id}/delete_messages
        </code></pre>
        <pre><code>
        {
            "messages": [
                {
                    "id": "message_id"
                },
                {
                    "id": "message_id"
                },
                {
                    "id": "message_id"
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
        message_dicts = request.data.get('messages', [])
        # Todo: validate message ids
        message_ids = [str(m.get('id')) for m in message_dicts]
        messages = Message.objects.filter(conversation_id=conversation.id, id__in=message_ids)
        message_controller.hide_messages_from_user(messages, request.user)
        ret = {
            'data': {
                'success': _("The messages have been deleted"),
                'deleted_messages': [{'id': m} for m in message_ids]
            },
            'status': status.HTTP_202_ACCEPTED
        }
        return Response(**ret)

    @detail_route(methods=['post', 'delete'], suffix='Read')
    def read(self, request, *args, **kwargs):
        """
        Mark the conversation as read/unread
        ###REQUIRES AUTH
        Marking a conversation as read will mark `all` its messages as read as well. On the other hand, marking it as unread will only mark its `last_message` as unread.
        ---
        omit_serializer: true
        omit_parameters:
            - form
        """
        conversation = self.get_object()
        if request.method == 'POST':
            conversation.mark_as_read(request.user)
        elif request.method == 'DELETE':
            conversation.mark_as_unread(request.user)
        return Response(status=status.HTTP_202_ACCEPTED)

    @detail_route(methods=['post'], suffix='Reply')
    def reply(self, request, *args, **kwargs):
        """
        Reply in a conversation
        ###REQUIRES AUTH
        ###Request
        ####Body
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
                    "profile": {
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
                    "videos": [] // list of {Video Object}s
                }
            ]
        }
        </code></pre>

        Either `text`, `attachments` or both has to be provided. Images and videos are to be compressed and uploaded before submitting. CDN urls should be sent.
        ---
        response_serializer: MessageSerializer
        omit_parameters:
            - form
        parameters:
            - name: body
              paramType: body
        """
        context = {
            'request': request,
            'conversation': self.get_object()
        }
        serializer = MessageSerializer(data=request.data, partial=True, context=context)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        headers = self.get_success_message_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    @detail_route(methods=['post'], suffix='Add Profile')
    def add_profile(self, request, *args, **kwargs):
        """
        Add profile to this conversation.
        ###REQUIRES AUTH
        The logged in profile should be admin in the conversation and the newly added profile should be one of his listeners.
        ###Request
        ####Body
        <pre><code>
        {
            "profile": {
                "id": "id of the profile to be added"
            }
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
        # Todo (mo): utilize self.get_serializer(instance=conversation, data=request.data)
        context = {
            'conversation': self.get_object(),
            'request': request
        }
        serializer = AddProfileSerializer(data=request.data, context=context)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_202_ACCEPTED)

    @detail_route(methods=['post'], suffix='Remove Profile')
    def remove_profile(self, request, *args, **kwargs):
        """
        Remove profile from this conversation.
        ###REQUIRES AUTH
        The logged in profile should be admin in the conversation.
        ###Request
        ####Body
        <pre><code>
        {
            "profile": {
                "id": "id of the profile to be removed"
            }
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
        context = {
            'conversation': self.get_object(),
            'request': request
        }
        serializer = RemoveProfileSerializer(data=request.data, context=context)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_202_ACCEPTED)

    @detail_route(methods=['post'], suffix='Promote Profile to Admin')
    def promote_admin(self, request, *args, **kwargs):
        """
        Promote profile to admin in this conversation
        ###REQUIRES AUTH
        The logged in profile should be admin in the conversation.
        ###Request
        ####Body
        <pre><code>
        {
            "profile": {
                "id": "id of the profile to be promoted as admin"
            }
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
        context = {
            'conversation': self.get_object(),
            'request': request
        }
        serializer = PromoteAdminSerializer(data=request.data, context=context)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_202_ACCEPTED)

    @detail_route(methods=['post'], suffix='Block Profile')
    def block_profile(self, request, *args, **kwargs):
        """
        Block profile from this conversation
        ###REQUIRES AUTH
        The logged in profile should be admin in the conversation.
        ###Request
        ####Body
        <pre><code>
        {
            "profile": {
                "id": "id of the profile to be blocked"
            }
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
        context = {
            'conversation': self.get_object(),
            'request': request
        }
        serializer = BlockProfileSerializer(data=request.data, context=context)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_202_ACCEPTED)

    @detail_route(methods=['post'], suffix='Unblock Profile')
    def unblock_profile(self, request, *args, **kwargs):
        """
        Unblock profile from this conversation
        ###REQUIRES AUTH
        The logged in profile should be admin in the conversation.
        ###Request
        ####Body
        <pre><code>
        {
            "profile": {
                "id": "id of the profile to be unblocked"
            }
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
        context = {
            'conversation': self.get_object(),
            'request': request
        }
        serializer = UnblockProfileSerializer(data=request.data, context=context)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_202_ACCEPTED)

    @detail_route(methods=['get'], suffix='Blocked Profiles')
    def blocked(self, request, *args, **kwargs):
        """
        List blocked profiles from this conversation
        ###REQUIRES AUTH
        The logged in profile should be admin in the conversation.
        ###Response
        <pre><code>
        {
          "next": null, // next results page url
          "previous": null, // previous results page url
          "results": [] // list of {ProfileSerializer}
        }
        </code></pre>
        ---
        serializer: ProfileSerializer
        omit_parameters:
            - form
        parameters:
            - name: page
              paramType: query
            - name: page_size
              paramType: query
        """
        conversation = self.get_object()
        blocked = User.objects.filter(id__in=conversation.blocked)
        self.pagination_class = ShoutitPageNumberPagination
        page = self.paginate_queryset(blocked)
        serializer = ProfileSerializer(page, many=True, context={'request': request})
        return self.get_paginated_response(serializer.data)

    def get_success_message_headers(self, data):
        loc = reverse('conversation-messages', kwargs={'id': data['conversation_id']}, request=self.request)
        return {'Location': loc}


class MessageViewSet(UUIDViewSetMixin, mixins.DestroyModelMixin, viewsets.GenericViewSet):
    """
    Message API Resource.
    """
    serializer_class = MessageSerializer
    permission_classes = (permissions.IsAuthenticated, CanContribute)

    def get_queryset(self):
        return Message.objects.all()

    @detail_route(methods=['post', 'delete'], suffix='Read')
    def read(self, request, *args, **kwargs):
        """
        Mark the message as read/unread
        ###REQUIRES AUTH
        Marking a message as read will trigger a `new_read_by` event on conversation pusher channel.
        ---
        omit_serializer: true
        omit_parameters:
            - form
        """
        message = self.get_object()
        # Skip reading / unreading own messages
        if request.user.id != message.user_id:
            if request.method == 'POST':
                message.mark_as_read(request.user)
            elif request.method == 'DELETE':
                message.mark_as_unread(request.user)
        return Response(status=status.HTTP_202_ACCEPTED)


class PublicChatViewSet(DetailSerializerMixin, UUIDViewSetMixin, mixins.ListModelMixin, mixins.CreateModelMixin,
                        viewsets.GenericViewSet):
    """
    Public Chat API Resource.
    """
    serializer_class = ConversationDetailSerializer
    serializer_detail_class = ConversationDetailSerializer
    pagination_class = ReverseModifiedDateTimePagination
    permission_classes = (permissions.IsAuthenticated, CanContribute)

    def get_queryset(self, *args, **kwargs):
        serializer_compat(self)

        user = self.request.user
        filters = {
            'type': CONVERSATION_TYPE_PUBLIC_CHAT,
            'country': user.location['country']
        }
        related = ['last_message__user']
        exclude = {'blocked__contains': [user.id]}
        order = '-modified_at'
        return Conversation.objects.filter(**filters).exclude(**exclude).select_related(*related).order_by(order)

    def list(self, request, *args, **kwargs):
        """
        List Public Chat conversations in profile's country.
        ###REQUIRES AUTH
        [Conversations Pagination](https://github.com/shoutit/shoutit-api/wiki/Messaging-Pagination#conversations-pagination)
        ---
        serializer: ConversationDetailSerializer
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
        return super(PublicChatViewSet, self).list(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        """
        Create Public Chat conversation in profile's country.
        ###REQUIRES AUTH
        ####Body
        <pre><code>
        {
            "subject": "text goes here",
            "icon": "icon url"
        }
        </code></pre>
        ---
        serializer: ConversationDetailSerializer
        omit_parameters:
            - form
        parameters:
            - name: body
              paramType: body
        """
        self.serializer_class = ConversationDetailSerializer
        return super(PublicChatViewSet, self).create(request, *args, **kwargs)
