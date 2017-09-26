"""

"""
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import ugettext_lazy as _
from rest_framework import serializers

from common.constants import REPORT_TYPE_PROFILE, REPORT_TYPE_SHOUT, REPORT_TYPE_CONVERSATION
from common.utils import any_in
from shoutit.api.serializers import HasAttachedUUIDObjects
from shoutit.models import Notification, Report
from shoutit.utils import blank_to_none
from .conversation import ConversationDetailSerializer
from .message import MessageSerializer
from .profile import ProfileSerializer
from .shout import ShoutSerializer
from ..exceptions import ERROR_REASON


class AttachedObjectSerializer(HasAttachedUUIDObjects, serializers.Serializer):
    profile = ProfileSerializer(source='attached_profile', required=False)
    message = MessageSerializer(source='attached_message', required=False)
    shout = ShoutSerializer(source='attached_shout', required=False)
    conversation = ConversationDetailSerializer(source='attached_conversation', required=False)

    def to_representation(self, attached_object):
        # Create reference to the object inside itself with attr based on its class `attached_{class name}`
        class_name = getattr(attached_object, 'model_name', None)
        if class_name == 'User':
            setattr(attached_object, 'attached_profile', attached_object)
        elif class_name:
            setattr(attached_object, 'attached_%s' % class_name.lower(), attached_object)
        return super(AttachedObjectSerializer, self).to_representation(attached_object)

    def to_internal_value(self, data):
        ret = super(AttachedObjectSerializer, self).to_internal_value(data)
        keys = data.keys()
        if len(keys) != 1:
            raise serializers.ValidationError((_("Should have a single property"), ERROR_REASON.REQUIRED))
        return ret


class NotificationSerializer(serializers.ModelSerializer):
    created_at = serializers.IntegerField(source='created_at_unix')
    type = serializers.CharField(source='get_type_display')
    attached_object = AttachedObjectSerializer(help_text="To be deprecated!")

    class Meta:
        model = Notification
        fields = ('id', 'created_at', 'is_read', 'display', 'app_url', 'web_url', 'type', 'attached_object')

    def to_representation(self, instance):
        ret = super(NotificationSerializer, self).to_representation(instance)
        blank_to_none(ret['display'], ['text', 'image'])
        return ret


class ReportSerializer(serializers.ModelSerializer):
    created_at = serializers.IntegerField(source='created_at_unix', read_only=True)
    type = serializers.CharField(source='get_type_display', read_only=True)
    profile = ProfileSerializer(source='user', read_only=True)
    attached_object = AttachedObjectSerializer(help_text="The reported object")

    class Meta:
        model = Report
        fields = ('id', 'created_at', 'type', 'profile', 'text', 'attached_object')

    def to_internal_value(self, data):
        validated_data = super(ReportSerializer, self).to_internal_value(data)
        attached_object = validated_data['attached_object']

        if not any_in(['attached_profile', 'attached_shout', 'attached_conversation'], attached_object):
            error_tuple = (_("Should have either 'profile', 'shout' or 'conversation'"), ERROR_REASON.REQUIRED)
            raise serializers.ValidationError({'attached_object': error_tuple})

        if 'attached_profile' in attached_object:
            validated_data['type'] = REPORT_TYPE_PROFILE

        elif 'attached_shout' in attached_object:
            validated_data['type'] = REPORT_TYPE_SHOUT

        elif 'attached_conversation' in attached_object:
            validated_data['type'] = REPORT_TYPE_CONVERSATION

        return validated_data

    def create(self, validated_data):
        report_type = validated_data['type']
        if report_type == REPORT_TYPE_PROFILE:
            model_name = 'user'
        else:
            model_name = str(report_type)
        user = self.root.context['request'].user
        text = validated_data.get('text')
        object_id = validated_data['attached_object']['attached_%s' % report_type]['id']
        ct = ContentType.objects.get_by_natural_key('shoutit', model_name)
        report = Report.objects.create(user=user, text=text, content_type=ct, object_id=object_id, type=report_type)
        return report

    def to_representation(self, instance):
        ret = super(ReportSerializer, self).to_representation(instance)
        blank_to_none(ret, ['text'])
        return ret
