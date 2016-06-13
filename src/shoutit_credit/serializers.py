"""

"""
from __future__ import unicode_literals

from rest_framework import serializers
from .models import PromoteShouts, CreditTransaction, PromoteLabel, ShoutPromotion

from shoutit.api.v3.serializers import AttachedUUIDObjectMixin


class CreditTransactionSerializer(serializers.ModelSerializer):
    created_at = serializers.IntegerField(source='created_at_unix')
    type = serializers.CharField(source='get_type_display')

    class Meta:
        model = CreditTransaction
        fields = ('id', 'created_at', 'display', 'app_url', 'web_url', 'type')


class PromoteLabelSerializer(serializers.ModelSerializer):
    class Meta:
        model = PromoteLabel
        fields = ('name', 'description', 'color', 'bg_color')


class PromoteOptionSerializer(serializers.ModelSerializer, AttachedUUIDObjectMixin):
    label = PromoteLabelSerializer(read_only=True)

    class Meta:
        model = PromoteShouts
        fields = ('id', 'name', 'description', 'label', 'credits', 'days')
        extra_kwargs = {'name': {'read_only': True}, 'description': {'read_only': True}}

    def to_internal_value(self, data):
        # Validate when passed as attached object
        ret = self.to_internal_attached_value(data, force_validation=True)
        if ret:
            return ret

        validated_data = super(PromoteOptionSerializer, self).to_internal_value(data)
        return validated_data


class PromoteShoutSerializer(serializers.Serializer):
    option = PromoteOptionSerializer()

    def update(self, instance, validated_data):
        option = self.fields['option'].instance
        user = self.context['request'].user
        option.apply(shout=instance, user=user)
        return instance

    def to_representation(self, instance):
        return {
            'success': 'The shout was successfully promoted',
            'promotion': ShoutPromotionSerializer(instance.promotion).data
        }


class ShoutPromotionSerializer(serializers.ModelSerializer, AttachedUUIDObjectMixin):
    label = PromoteLabelSerializer(read_only=True)

    class Meta:
        model = ShoutPromotion
        fields = ('id', 'label', 'days', 'expires_at')
        extra_kwargs = {'expires_at': {'source': 'expires_at_unix'}}
