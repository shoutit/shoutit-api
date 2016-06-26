"""

"""
from __future__ import unicode_literals

from django.utils.translation import ugettext_lazy as _
from rest_framework import serializers, exceptions as drf_exceptions
from rest_framework.reverse import reverse

from common.constants import (ConversationType, CONVERSATION_TYPE_ABOUT_SHOUT, CONVERSATION_TYPE_PUBLIC_CHAT)
from shoutit.api.serializers import AttachedUUIDObjectMixin, HasAttachedUUIDObjects
from shoutit.controllers import message_controller
from shoutit.models import Conversation
from shoutit.utils import blank_to_none
from .base import LocationSerializer
from .message import MessageSerializer
from .profile import ProfileSerializer, MiniProfileSerializer
from .shout import ShoutSerializer
from .. import exceptions


class ConversationSerializer(AttachedUUIDObjectMixin, serializers.ModelSerializer):
    modified_at = serializers.IntegerField(source='modified_at_unix', read_only=True)
    api_url = serializers.HyperlinkedIdentityField(view_name='conversation-detail', lookup_field='id')
    type = serializers.ChoiceField(choices=ConversationType.texts, source='get_type_display',
                                   default=str(CONVERSATION_TYPE_PUBLIC_CHAT),
                                   help_text="'chat', 'about_shout' or 'public_chat'")
    display = serializers.SerializerMethodField(help_text="Properties used for displaying the conversation")
    location = LocationSerializer(help_text="Defaults to user's saved location, Passing the `latitude` and `longitude` "
                                            "is enough to calculate new location properties", required=False)
    unread_messages_count = serializers.SerializerMethodField(help_text="# of unread messages in this conversation")
    messages_url = serializers.SerializerMethodField(help_text="URL to get the messages of this conversation")
    reply_url = serializers.SerializerMethodField(help_text="URL to reply in this conversation")

    class Meta:
        model = Conversation
        fields = ['id', 'modified_at', 'api_url', 'type', 'display', 'location', 'unread_messages_count',
                  'messages_url', 'reply_url']

    def get_unread_messages_count(self, instance):
        return instance.unread_messages(self.context['request'].user).count()

    def get_display(self, instance):
        return instance.display(self.context['request'].user)

    def get_messages_url(self, conversation):
        return reverse('conversation-messages', kwargs={'id': conversation.id}, request=self.context['request'])

    def get_reply_url(self, conversation):
        return reverse('conversation-reply', kwargs={'id': conversation.id}, request=self.context['request'])

    def validate_type(self, conversation_type):
        if conversation_type != 'public_chat':
            raise serializers.ValidationError({'type': _("Only 'public_chat' conversations can be directly created")})
        return conversation_type

    def to_representation(self, instance):
        ret = super(ConversationSerializer, self).to_representation(instance)
        blank_to_none(ret, ['icon', 'subject'])
        blank_to_none(ret['display'], ['title', 'sub_title', 'image'])
        if ret['type'] != str(CONVERSATION_TYPE_PUBLIC_CHAT):
            del ret['location']
        return ret


class ConversationDetailSerializer(ConversationSerializer):
    created_at = serializers.IntegerField(source='created_at_unix', read_only=True)
    creator = MiniProfileSerializer(read_only=True, help_text='Can be `null` when the conversation was created by the'
                                                              ' system')
    subject = serializers.CharField(max_length=25, write_only=True)
    icon = serializers.URLField(allow_blank=True, max_length=200, required=False, write_only=True)
    about = serializers.SerializerMethodField(help_text="Only set if the conversation of type 'about_shout'")
    profiles = ProfileSerializer(many=True, source='contributors', help_text="List of users in this conversations",
                                 read_only=True)
    # Deprecate
    last_message = MessageSerializer(read_only=True)

    class Meta(ConversationSerializer.Meta):
        parent_fields = ConversationSerializer.Meta.fields
        fields = parent_fields + [
            'created_at', 'web_url', 'app_url', 'messages_count',
            'subject', 'icon', 'creator', 'admins', 'profiles', 'blocked', 'last_message', 'attachments_count', 'about'
        ]

    def get_about(self, instance):
        if instance.type == CONVERSATION_TYPE_ABOUT_SHOUT:
            return ShoutSerializer(instance.attached_object, context=self.root.context).data
        return None

    def create(self, validated_data):
        user = self.context['request'].user
        conversation_type = ConversationType.texts[validated_data['get_type_display']]
        if conversation_type == CONVERSATION_TYPE_PUBLIC_CHAT:
            subject = validated_data['subject']
            icon = validated_data.get('icon')
            location = validated_data.get('location')
            conversation = message_controller.create_public_chat(user, subject, icon, location)
        else:
            raise exceptions.InvalidBody('type', _('Only `public_chat` is allowed'))
        return conversation

    def update(self, conversation, validated_data):
        subject = validated_data.get('subject')
        icon = validated_data.get('icon')
        if subject:
            conversation.subject = subject
        if icon:
            conversation.icon = icon
        if subject or icon:
            conversation.save(update_fields=['subject', 'icon'])
        return conversation


class ConversationProfileActionSerializer(HasAttachedUUIDObjects, serializers.Serializer):
    """
    Should be initialized in Conversation view with
    context = {
        'conversation': self.get_object(),
        'request': request
    }
    Subclasses must
    - Define these attributes
    `success_message`, `error_message`
    - Implement these methods
    `condition(self, conversation, actor, profile)`, `create(self, validated_data)`
    """
    profile = ProfileSerializer()

    def to_internal_value(self, data):
        conversation = self.context['conversation']
        request = self.context['request']
        actor = request.user
        if actor.id not in conversation.admins:
            raise drf_exceptions.PermissionDenied()

        validated_data = super(ConversationProfileActionSerializer, self).to_internal_value(data)
        profile = self.fields['profile'].instance

        if actor.id == profile.id:
            raise exceptions.ShoutitBadRequest(_("You can't make chat actions against your own profile"),
                                               reason=exceptions.ERROR_REASON.BAD_REQUEST)
        if not self.condition(conversation, actor, profile):
            raise exceptions.InvalidBody('profile', self.error_message % {'name': profile.name})

        return validated_data

    def to_representation(self, instance):
        profile = self.fields['profile'].instance
        return {'success': self.success_message % {'name': profile.name}}

    # Todo (mo): utilize update instead of create. update has the conversation instance from the view
    # A better and more general example is done in `ObjectProfileActionSerializer`
    def update(self, instance, validated_data):
        return self.create(validated_data=validated_data)

    def create(self, validated_data):
        raise NotImplementedError('`create()` must be implemented.')


class AddProfileSerializer(ConversationProfileActionSerializer):
    error_message = _("%(name)s is not one of your listeners and can't be added to this conversation")
    success_message = _("Added %(name)s to this conversation")

    def condition(self, conversation, actor, profile):
        return profile.is_listening(actor)

    def create(self, validated_data):
        conversation = self.context['conversation']
        profile = self.fields['profile'].instance
        if not conversation.users.filter(id=profile.id).exists():
            conversation.add_profile(profile)
        else:
            self.success_message = "%s is already in this conversation"
        return conversation


class RemoveProfileSerializer(ConversationProfileActionSerializer):
    error_message = _("%(name)s is not a member of this conversation and can't be removed from it")
    success_message = _("Removed %(name)s from this conversation")

    def condition(self, conversation, actor, profile):
        return conversation.users.filter(id=profile.id).exists()

    def create(self, validated_data):
        conversation = self.context['conversation']
        profile = self.fields['profile'].instance
        conversation.remove_profile(profile)
        return conversation


class PromoteAdminSerializer(ConversationProfileActionSerializer):
    error_message = _("%(name)s is not a member of this conversation and can't be promoted to admin it")
    success_message = _("Promoted %(name)s to admin in this conversation")

    def condition(self, conversation, actor, profile):
        return conversation.users.filter(id=profile.id).exists()

    def create(self, validated_data):
        conversation = self.context['conversation']
        profile = self.fields['profile'].instance
        if profile.id not in conversation.admins:
            conversation.promote_admin(profile)
        else:
            self.success_message = _("%(name)s is already admin in this conversation")
        return conversation


class BlockProfileSerializer(ConversationProfileActionSerializer):
    error_message = _("%(name)s is not a member of this conversation and can't be blocked")
    success_message = _("Blocked %(name)s from this conversation")

    def condition(self, conversation, actor, profile):
        return conversation.users.filter(id=profile.id).exists()

    def create(self, validated_data):
        conversation = self.context['conversation']
        profile = self.fields['profile'].instance
        if profile.id not in conversation.blocked:
            conversation.block_profile(profile)
        else:
            self.success_message = _("%(name)s is already blocked from this conversation")
        return conversation


class UnblockProfileSerializer(ConversationProfileActionSerializer):
    error_message = _("%(name)s is not blocked from this conversation")
    success_message = _("Unblocked %(name)s from this conversation")

    def condition(self, conversation, actor, profile):
        return profile.id in conversation.blocked

    def create(self, validated_data):
        conversation = self.context['conversation']
        profile = self.fields['profile'].instance
        conversation.unblock_profile(profile)
        return conversation
