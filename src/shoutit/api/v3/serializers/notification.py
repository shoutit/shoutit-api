"""

"""
from __future__ import unicode_literals

from collections import OrderedDict

from rest_framework import serializers

from common.constants import REPORT_TYPE_PROFILE, REPORT_TYPE_SHOUT
from shoutit.models import Notification, Report, User, Shout
from shoutit.utils import blank_to_none
from .message import MessageSerializer
from .profile import ProfileSerializer
from .shout import ShoutSerializer
from ..exceptions import ERROR_REASON


class AttachedObjectSerializer(serializers.Serializer):
    profile = ProfileSerializer(source='attached_profile', required=False)
    message = MessageSerializer(source='attached_message', required=False)
    shout = ShoutSerializer(source='attached_shout', required=False)

    def to_representation(self, attached_object):
        # create reference to the object inside itself with name based on its class
        # to be used for representation
        class_name = attached_object.__class__.__name__
        if class_name == 'User':
            setattr(attached_object, 'attached_profile', attached_object)
        if class_name == 'Profile' or class_name == 'Page':
            setattr(attached_object, 'attached_profile', attached_object.user)
        if class_name == 'Message':
            setattr(attached_object, 'attached_message', attached_object)
        if class_name == 'Shout':
            setattr(attached_object, 'attached_shout', attached_object)

        return super(AttachedObjectSerializer, self).to_representation(attached_object)


class NotificationSerializer(serializers.ModelSerializer):
    created_at = serializers.IntegerField(source='created_at_unix')
    type = serializers.CharField(source='get_type_display', help_text="Currently, either 'listen' or 'message'")
    attached_object = AttachedObjectSerializer(
        help_text="Attached Object that contain either 'profile' or 'message' objects depending on notification type")

    class Meta:
        model = Notification
        fields = ('id', 'type', 'created_at', 'is_read', 'attached_object')


class ReportSerializer(serializers.ModelSerializer):
    created_at = serializers.IntegerField(source='created_at_unix', read_only=True)
    type = serializers.CharField(source='get_type_display', help_text="Currently, either 'profile' or 'shout'",
                                 read_only=True)
    profile = ProfileSerializer(source='user', read_only=True)
    attached_object = AttachedObjectSerializer(
        help_text="Attached Object that contain either 'profile' or 'shout' objects depending on report type")

    class Meta:
        model = Report
        fields = ('id', 'created_at', 'type', 'profile', 'text', 'attached_object')

    def to_internal_value(self, data):
        validated_data = super(ReportSerializer, self).to_internal_value(data)

        errors = OrderedDict()
        if 'attached_object' in validated_data:
            attached_object = validated_data['attached_object']
            if not ('attached_profile' in attached_object or 'attached_shout' in attached_object):
                error_tuple = ("attached_object should have either 'profile' or 'shout'", ERROR_REASON.REQUIRED)
                errors['attached_object'] = error_tuple

            if 'attached_profile' in attached_object:
                validated_data['type'] = REPORT_TYPE_PROFILE

            if 'attached_shout' in attached_object:
                validated_data['type'] = REPORT_TYPE_SHOUT
        else:
            error_tuple = ("This field is required", ERROR_REASON.REQUIRED)
            errors['attached_object'] = error_tuple
        if errors:
            raise serializers.ValidationError(errors)

        return validated_data

    def create(self, validated_data):
        attached_object = None
        report_type = validated_data['type']

        if report_type == REPORT_TYPE_PROFILE:
            attached_object = User.objects.get(id=validated_data['attached_object']['attached_profile']['id'])
        if report_type == REPORT_TYPE_SHOUT:
            attached_object = Shout.objects.get(id=validated_data['attached_object']['attached_shout']['id'])
        text = validated_data['text'] if 'text' in validated_data else None
        report = Report.objects.create(user=self.root.context['request'].user, text=text,
                                       attached_object=attached_object, type=report_type)
        return report

    def to_representation(self, instance):
        ret = super(ReportSerializer, self).to_representation(instance)
        blank_to_none(ret, ['text'])
        return ret
