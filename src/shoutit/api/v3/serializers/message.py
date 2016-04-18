"""

"""
from __future__ import unicode_literals

from collections import OrderedDict

from rest_framework import serializers
from rest_framework.reverse import reverse

from common.constants import (MESSAGE_ATTACHMENT_TYPE_SHOUT, MESSAGE_ATTACHMENT_TYPE_LOCATION,
                              MESSAGE_ATTACHMENT_TYPE_MEDIA, ConversationType, CONVERSATION_TYPE_ABOUT_SHOUT,
                              MessageAttachmentType)
from common.utils import any_in
from shoutit.controllers import location_controller, message_controller
from shoutit.models import Message, SharedLocation, Conversation, MessageAttachment
from shoutit.utils import blank_to_none
from .base import VideoSerializer
from .profile import ProfileSerializer
from .shout import ShoutSerializer


class SharedLocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = SharedLocation
        fields = ['latitude', 'longitude']


class MessageAttachmentSerializer(serializers.ModelSerializer):
    type = serializers.ChoiceField(choices=MessageAttachmentType.texts, source='get_type_display', read_only=True)
    shout = ShoutSerializer(required=False)
    location = SharedLocationSerializer(required=False)
    images = serializers.ListField(child=serializers.URLField(), required=False)
    videos = VideoSerializer(many=True, required=False)

    class Meta:
        model = MessageAttachment
        fields = ['type', 'shout', 'location', 'images', 'videos']

    def to_representation(self, instance):
        ret = super(MessageAttachmentSerializer, self).to_representation(instance)
        if instance.type == MESSAGE_ATTACHMENT_TYPE_SHOUT:
            del ret['location']
            del ret['images']
            del ret['videos']
        if instance.type == MESSAGE_ATTACHMENT_TYPE_LOCATION:
            del ret['shout']
            del ret['images']
            del ret['videos']
        if instance.type == MESSAGE_ATTACHMENT_TYPE_MEDIA:
            del ret['location']
            del ret['shout']
        return ret


class MessageSerializer(serializers.ModelSerializer):
    conversation_id = serializers.UUIDField(read_only=True)
    profile = ProfileSerializer(source='user', read_only=True)
    created_at = serializers.IntegerField(source='created_at_unix', read_only=True)
    attachments = MessageAttachmentSerializer(many=True, required=False)
    read_by = serializers.ListField(source='read_by_objects', read_only=True)

    class Meta:
        model = Message
        fields = ('id', 'created_at', 'conversation_id', 'profile', 'text', 'attachments', 'read_by')

    def to_internal_value(self, data):
        validated_data = super(MessageSerializer, self).to_internal_value(data)
        attachments = validated_data.get('attachments')
        text = validated_data.get('text')
        errors = OrderedDict()

        if not text and not attachments:
            # Todo: check why having string as the detail results in exception
            # raise serializers.ValidationError("Provide 'text' or 'attachments'")
            raise serializers.ValidationError({'': "Provide 'text' or 'attachments'"})

        if attachments is not None:
            if isinstance(attachments, list) and len(attachments):
                i = 0
                errors['attachments'] = []
                for attachment in attachments:
                    attachment_error = None
                    if not any_in(['shout', 'location', 'images', 'videos'], attachment):
                        attachment_error = {'': "attachment should have at least a 'shout', 'location', 'images' or 'videos'"}
                        errors['attachments'].insert(i, attachment_error)
                        i += 1
                        continue

                    if 'location' in attachment and ('latitude' not in attachment['location'] or 'longitude' not in attachment['location']):
                        attachment_error = {'location': "location object should have 'latitude' and 'longitude'"}

                    if 'images' in attachment or 'videos' in attachment:
                        images = attachment.get('images')
                        videos = attachment.get('videos')
                        if not (images or videos):
                            attachment_error = {
                                '': "attachment should have at least one item in a 'images' or 'videos'"}
                    errors['attachments'].insert(i, attachment_error or None)
                    i += 1
                if not any(errors['attachments']):
                    del errors['attachments']

        if text is not None and text == "" and attachments is None:
            errors['text'] = "text can not be empty"

        # Todo: Raise errors directly that is fine
        if errors:
            raise serializers.ValidationError(errors)

        return validated_data

    def to_representation(self, instance):
        ret = super(MessageSerializer, self).to_representation(instance)
        blank_to_none(ret, ['text'])

        # Client id, Todo: check if it is still used by any client
        request = self.root.context.get('request')
        if request and request.method == 'POST':
            data = getattr(request, 'data', {})
            client_id = data.get('client_id')
            if client_id:
                ret['client_id'] = request.data.get('client_id')
        return ret

    def create(self, validated_data):
        request = self.root.context.get('request')
        user = getattr(request, 'user', None)
        page_admin_user = getattr(request, 'page_admin_user', None)
        conversation = self.root.context.get('conversation')
        to_users = self.root.context.get('to_users')
        about = self.root.context.get('about')
        text = validated_data.get('text')
        attachments = validated_data.get('attachments')
        message = message_controller.send_message(conversation, user, to_users=to_users, about=about, text=text,
                                                  attachments=attachments, request=request,
                                                  page_admin_user=page_admin_user)
        return message


class ConversationSerializer(serializers.ModelSerializer):
    profiles = ProfileSerializer(many=True, source='contributors', help_text="List of users in this conversations",
                                 read_only=True)
    last_message = MessageSerializer(required=False)
    type = serializers.ChoiceField(choices=ConversationType.texts, source='get_type_display',
                                   help_text="'chat', 'about_shout' or 'public_chat'")
    created_at = serializers.IntegerField(source='created_at_unix', read_only=True)
    modified_at = serializers.IntegerField(source='modified_at_unix', read_only=True)
    subject = serializers.CharField(max_length=25)
    about = serializers.SerializerMethodField(help_text="Only set if the conversation of type 'about_shout'")
    unread_messages_count = serializers.SerializerMethodField(
        help_text="Number of unread messages in this conversation")
    messages_url = serializers.SerializerMethodField(help_text="URL to get the messages of this conversation")
    reply_url = serializers.SerializerMethodField(help_text="URL to reply in this conversation")

    class Meta:
        model = Conversation
        fields = ('id', 'created_at', 'modified_at', 'web_url', 'type', 'messages_count', 'unread_messages_count',
                  'subject', 'icon', 'admins', 'profiles', 'last_message', 'about', 'messages_url', 'reply_url')

    def get_about(self, instance):
        if instance.type == CONVERSATION_TYPE_ABOUT_SHOUT:
            return ShoutSerializer(instance.attached_object, context=self.root.context).data
        return None

    def get_unread_messages_count(self, instance):
        return instance.unread_messages_count(self.context['request'].user)

    def get_messages_url(self, conversation):
        return reverse('conversation-messages', kwargs={'id': conversation.id}, request=self.context['request'])

    def get_reply_url(self, conversation):
        return reverse('conversation-reply', kwargs={'id': conversation.id}, request=self.context['request'])

    def to_internal_value(self, data):
        validated_data = super(ConversationSerializer, self).to_internal_value(data)
        return validated_data

    def validate_type(self, conversation_type):
        if conversation_type != 'public_chat':
            raise serializers.ValidationError({'type': "Only 'public_chat' conversations can be directly created"})
        return conversation_type

    def create(self, validated_data):
        user = self.context['request'].user
        conversation_type = ConversationType.texts[validated_data['get_type_display']]
        subject = validated_data['subject']
        icon = validated_data.get('icon', '')
        conversation = Conversation(creator=user, type=conversation_type, subject=subject, icon=icon, admins=[user.id])
        location_controller.update_object_location(conversation, user.location, save=False)
        conversation.save()
        conversation.users.add(user)
        return conversation
