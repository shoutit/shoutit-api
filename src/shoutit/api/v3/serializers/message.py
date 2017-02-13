"""

"""
from collections import OrderedDict

from django.utils.translation import ugettext_lazy as _
from rest_framework import serializers

from common.constants import (MESSAGE_ATTACHMENT_TYPE_SHOUT, MESSAGE_ATTACHMENT_TYPE_LOCATION,
                              MESSAGE_ATTACHMENT_TYPE_MEDIA, MessageAttachmentType, MESSAGE_ATTACHMENT_TYPE_PROFILE)
from common.utils import any_in
from shoutit.api.serializers import AttachedUUIDObjectMixin, HasAttachedUUIDObjects
from shoutit.controllers import message_controller
from shoutit.models import Message, SharedLocation, MessageAttachment
from shoutit.utils import blank_to_none
from .base import VideoSerializer
from .profile import ProfileSerializer
from .shout import ShoutSerializer


class SharedLocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = SharedLocation
        fields = ['latitude', 'longitude']


class MessageAttachmentSerializer(HasAttachedUUIDObjects, serializers.ModelSerializer):
    type = serializers.ChoiceField(choices=MessageAttachmentType.texts, source='get_type_display', read_only=True)
    shout = ShoutSerializer(required=False)
    location = SharedLocationSerializer(required=False)
    profile = ProfileSerializer(required=False)
    images = serializers.ListField(child=serializers.URLField(), required=False)
    videos = VideoSerializer(many=True, required=False)

    class Meta:
        model = MessageAttachment
        fields = ['type', 'shout', 'location', 'profile', 'images', 'videos']

    def to_representation(self, instance):
        ret = super(MessageAttachmentSerializer, self).to_representation(instance)
        if instance.type == MESSAGE_ATTACHMENT_TYPE_SHOUT:
            del ret['location']
            del ret['profile']
            del ret['images']
            del ret['videos']
        if instance.type == MESSAGE_ATTACHMENT_TYPE_LOCATION:
            del ret['shout']
            del ret['profile']
            del ret['images']
            del ret['videos']
        if instance.type == MESSAGE_ATTACHMENT_TYPE_PROFILE:
            del ret['shout']
            del ret['location']
            del ret['images']
            del ret['videos']
        if instance.type == MESSAGE_ATTACHMENT_TYPE_MEDIA:
            del ret['shout']
            del ret['location']
            del ret['profile']
        return ret


class MessageSerializer(AttachedUUIDObjectMixin, serializers.ModelSerializer):
    conversation_id = serializers.UUIDField(read_only=True)
    profile = ProfileSerializer(source='user', read_only=True)
    created_at = serializers.IntegerField(source='created_at_unix', read_only=True)
    attachments = MessageAttachmentSerializer(many=True, required=False)
    read_by = serializers.ListField(source='read_by_objects', read_only=True)

    class Meta:
        model = Message
        fields = ('id', 'created_at', 'conversation_id', 'app_url', 'profile', 'text', 'attachments', 'read_by')

    def to_internal_value(self, data):
        # Validate when passed as attached object or message attachment
        ret = self.to_internal_attached_value(data)
        if ret:
            return ret

        validated_data = super(MessageSerializer, self).to_internal_value(data)
        attachments = validated_data.get('attachments')
        text = validated_data.get('text')
        errors = OrderedDict()

        if not text and not attachments:
            # Todo: check why having string as the detail results in exception
            # raise serializers.ValidationError("Provide 'text' or 'attachments'")
            raise serializers.ValidationError({'': _("Provide 'text' or 'attachments'")})
        if attachments is not None:
            if isinstance(attachments, list) and len(attachments):
                i = 0
                errors['attachments'] = []
                valid_types = ['shout', 'location', 'profile', 'images', 'videos']
                types = ", ".join(map(str, valid_types))
                for attachment in attachments:
                    attachment_error = None

                    if not any_in(valid_types, attachment):
                        attachment_error = {'': _("Should have any of these properties: %(types)s") % {'types': types}}
                        errors['attachments'].insert(i, attachment_error)
                        i += 1
                        continue

                    if 'location' in attachment:
                        if 'latitude' not in attachment['location'] or 'longitude' not in attachment['location']:
                            attachment_error = {'location': _("location object should have 'latitude' and 'longitude'")}

                    if 'images' in attachment or 'videos' in attachment:
                        images = attachment.get('images')
                        videos = attachment.get('videos')
                        if not (images or videos):
                            attachment_error = {'': _("Should have at least one item in 'images' or 'videos'")}
                        # Todo (mo): passing `partial=False` should take care of videos validations
                        if videos:
                            for v in videos:
                                vs = VideoSerializer(data=v)
                                if not vs.is_valid():
                                    attachment_error = {'videos': str(vs.errors)}

                    errors['attachments'].insert(i, attachment_error or None)
                    i += 1
                if not any(errors['attachments']):
                    del errors['attachments']

        if text is not None and text == "" and attachments is None:
            errors['text'] = _("Can not be empty")

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
