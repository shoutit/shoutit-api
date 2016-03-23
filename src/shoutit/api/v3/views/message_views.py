# -*- coding: utf-8 -*-
"""

"""
from __future__ import unicode_literals

from rest_framework import permissions, viewsets, mixins, status
from rest_framework.decorators import detail_route
from rest_framework.exceptions import ValidationError, PermissionDenied
from rest_framework.response import Response
from rest_framework.reverse import reverse

from common.constants import CONVERSATION_TYPE_PUBLIC_CHAT
from shoutit.api.permissions import IsContributor, CanContribute
from shoutit.controllers import message_controller
from shoutit.models import Message, User, Conversation
from ..pagination import DateTimePagination, ReverseModifiedDateTimePagination
from ..serializers import ConversationSerializer, MessageSerializer
from ..views.viewsets import UUIDViewSetMixin


class ConversationViewSet(UUIDViewSetMixin, mixins.ListModelMixin, mixins.RetrieveModelMixin, mixins.CreateModelMixin,
                          viewsets.GenericViewSet):
    """
    Conversation API Resource.
    """
    serializer_class = ConversationSerializer
    pagination_class = ReverseModifiedDateTimePagination
    permission_classes = (permissions.IsAuthenticated, CanContribute)

    # todo: conversations / messages search

    def get_queryset(self, *args, **kwargs):
        if self._is_request_to_detail_endpoint():
            return Conversation.objects.all()
        else:
            conversation_type = self.request.query_params.get('type')
            if conversation_type == 'public_chat':
                filters = {
                    'type': CONVERSATION_TYPE_PUBLIC_CHAT,
                    'country': self.request.user.location['country']
                }
                return Conversation.objects.filter(**filters)
            else:
                return self.request.user.conversations.all().order_by('-modified_at')

    def _is_request_to_detail_endpoint(self):
        lookup = self.lookup_url_kwarg or self.lookup_field
        return lookup and lookup in self.kwargs

    def list(self, request, *args, **kwargs):
        """
        List the user conversations
        ###REQUIRES AUTH
        [Conversations Pagination](https://github.com/shoutit/shoutit-api/wiki/Messaging-Pagination#conversations-pagination)
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

    def retrieve(self, request, *args, **kwargs):
        """
        Retrieve a Conversation
        ###Example Response
        <pre><code>
        {
          "id": "73e43221-1f65-42c3-8c3e-82325a3e23ff",
          "created_at": 1458658338,
          "modified_at": 1458742115,
          "web_url": "http://shoutit.dev:8080/conversation/73e43221-1f65-42c3-8c3e-82325a3e23ff",
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
          "messages_url": "http://shoutit.dev:8000/v3/conversations/73e43221-1f65-42c3-8c3e-82325a3e23ff/messages",
          "reply_url": "http://shoutit.dev:8000/v3/conversations/73e43221-1f65-42c3-8c3e-82325a3e23ff/reply"
        }
        </code></pre>
        ---
        serializer: ConversationSerializer
        """
        return super(ConversationViewSet, self).retrieve(request, *args, **kwargs)

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
        messages_qs = conversation.get_messages_qs()
        self.pagination_class = DateTimePagination
        page = self.paginate_queryset(messages_qs)

        # only keep the messages that were not deleted by this user
        messages_ids = [message.id for message in page.object_list]
        deleted_messages_ids = request.user.deleted_messages.filter(id__in=messages_ids).values_list('id', flat=True)
        [page.object_list.remove(message) for message in page.object_list if message.id in deleted_messages_ids]

        serializer = MessageSerializer(page, many=True, context={'request': request})
        conversation.mark_as_read(request.user)
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
        message_ids = map(lambda x: str(x.get('id')), message_dicts)
        messages = Message.objects.filter(conversation_id=conversation.id, id__in=message_ids)
        message_controller.hide_messages_from_user(messages, request.user)
        ret = {
            'data': {
                'success': "You deleted these messages ",
                'deleted_messages': map(lambda m: {'id': m}, message_ids)
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

    @detail_route(methods=['post'], suffix='Add User')
    def add_user(self, request, *args, **kwargs):
        """
        Add user to this conversation.
        ###REQUIRES AUTH
        The logged in user should be admin in the conversation and the newly added user should be one of his listeners.
        ###Request
        ####Body
        <pre><code>
        {
            "user_id": "id of the user to be added"
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
        adder = request.user
        if adder.id not in conversation.admins:
            raise PermissionDenied()
        new_user_id = request.data.get('user_id')
        try:
            if not new_user_id:
                raise ValueError()
            new_user = User.objects.get(id=new_user_id)
        except User.DoesNotExist:
            raise ValidationError({'user_id': "user with id '%s' does not exist" % new_user_id})
        except:
            raise ValidationError({'user_id': "Invalid user_id"})
        if not new_user.is_listening(adder):
            raise ValidationError({'user_id': "The user you are trying to add is not one of your listeners"})
        conversation.users.add(new_user)
        return Response({'success': "Added '%s' to the conversation" % new_user.name}, status=status.HTTP_202_ACCEPTED)

    @detail_route(methods=['post'], suffix='Remove User')
    def remove_user(self, request, *args, **kwargs):
        """
        Remove user from this conversation.
        ###REQUIRES AUTH
        The logged in user should be admin in the conversation.
        ###Request
        ####Body
        <pre><code>
        {
            "user_id": "id of the user to be removed"
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
        adder = request.user
        if adder.id not in conversation.admins:
            raise PermissionDenied()
        existing_user_id = request.data.get('user_id')
        try:
            if not existing_user_id:
                raise ValueError()
            existing_user = User.objects.get(id=existing_user_id)
        except User.DoesNotExist:
            raise ValidationError({'user_id': "user with id '%s' does not exist" % existing_user_id})
        except:
            raise ValidationError({'user_id': "Invalid user_id"})
        if not conversation.users.filter(id=existing_user.id).exists():
            raise ValidationError({'user_id': "The user you are trying to remove is not a member of this conversation"})
        conversation.users.remove(existing_user)
        return Response({'success': "Removed '%s' from the conversation" % existing_user.name},
                        status=status.HTTP_202_ACCEPTED)

    @detail_route(methods=['post'], suffix='Promote User to admin')
    def promote_admin(self, request, *args, **kwargs):
        """
        Promote user to admin in this conversation.
        ###REQUIRES AUTH
        The logged in user should be admin in the conversation.
        ###Request
        ####Body
        <pre><code>
        {
            "user_id": "id of the user to be promoted"
        }
        </code></pre>x
        ---
        omit_serializer: true
        omit_parameters:
            - form
        parameters:
            - name: body
              paramType: body
        """
        conversation = self.get_object()
        adder = request.user
        if adder.id not in conversation.admins:
            raise PermissionDenied()
        existing_user_id = request.data.get('user_id')
        try:
            if not existing_user_id:
                raise ValueError()
            existing_user = User.objects.get(id=existing_user_id)
        except User.DoesNotExist:
            raise ValidationError({'user_id': "user with id '%s' does not exist" % existing_user_id})
        except:
            raise ValidationError({'user_id': "Invalid user_id"})
        if not conversation.users.filter(id=existing_user.id).exists():
            raise ValidationError(
                {'user_id': "The user you are trying to promote is not a member of this conversation"})
        conversation.admins.append(existing_user.pk)
        conversation.save()
        return Response({'success': "Promoted '%s' to admin in this conversation" % existing_user.name},
                        status=status.HTTP_202_ACCEPTED)

    def get_success_message_headers(self, data):
        loc = reverse('conversation-messages', kwargs={'id': data['conversation_id']}, request=self.request)
        return {'Location': loc}
