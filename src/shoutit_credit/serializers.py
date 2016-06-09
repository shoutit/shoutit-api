"""

"""
from __future__ import unicode_literals
from rest_framework import serializers

from shoutit_credit.models import CreditTransaction, PromoteLabel
from shoutit_credit.rules.shout import PromoteShouts


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


class PromoteOptionSerializer(serializers.ModelSerializer):
    label = PromoteLabelSerializer()

    class Meta:
        model = PromoteShouts
        fields = ('id', 'name', 'description', 'label', 'credits', 'days')
