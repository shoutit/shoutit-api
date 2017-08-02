"""

"""
from django.utils.translation import ugettext_lazy as _
from hvad.contrib.restframework import TranslatableModelSerializer
from rest_framework import serializers

from shoutit.api.serializers import AttachedUUIDObjectMixin, HasAttachedUUIDObjects
from shoutit_credit.models.profile import InvitationCode
from .models import PromoteShouts, CreditTransaction, PromoteLabel, ShoutPromotion


class CreditTransactionSerializer(serializers.ModelSerializer):
    created_at = serializers.IntegerField(source='created_at_unix')
    type = serializers.CharField(source='get_type_display')

    class Meta:
        model = CreditTransaction
        fields = ('id', 'created_at', 'display', 'app_url', 'web_url', 'type')


class PromoteLabelSerializer(TranslatableModelSerializer):
    name = serializers.CharField(read_only=True, source='_local_name')
    description = serializers.CharField(read_only=True, source='_local_description')

    class Meta:
        model = PromoteLabel
        fields = ('name', 'description', 'color', 'bg_color')


class PromoteOptionSerializer(AttachedUUIDObjectMixin, TranslatableModelSerializer):
    name = serializers.CharField(read_only=True, source='_local_name')
    description = serializers.CharField(read_only=True, source='_local_description')
    label = PromoteLabelSerializer(read_only=True)

    class Meta:
        model = PromoteShouts
        fields = ('id', 'name', 'description', 'label', 'credits', 'days')
        extra_kwargs = {'name': {'read_only': True}, 'description': {'read_only': True}}


class PromoteShoutSerializer(HasAttachedUUIDObjects, serializers.Serializer):
    option = PromoteOptionSerializer()

    def update(self, instance, validated_data):
        option = self.fields['option'].instance
        user = self.context['request'].user
        option.apply(shout=instance, user=user)
        return instance

    def to_representation(self, instance):
        return {
            'success': _('The shout has been promoted'),
            'promotion': ShoutPromotionSerializer(instance.promotion).data
        }


class ShoutPromotionSerializer(serializers.ModelSerializer):
    label = PromoteLabelSerializer(read_only=True)

    class Meta:
        model = ShoutPromotion
        fields = ('id', 'label', 'days', 'expires_at', 'is_expired')
        extra_kwargs = {'expires_at': {'source': 'expires_at_unix'}}


class InvitationCodeSerializer(serializers.ModelSerializer):
    created_at = serializers.IntegerField(source='created_at_unix', read_only=True)

    class Meta:
        model = InvitationCode
        fields = ('id', 'code', 'used_count', 'created_at')
