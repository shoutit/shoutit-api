"""

"""
from __future__ import unicode_literals
from rest_framework import serializers

from shoutit_credit.models import CreditTransaction


class CreditTransactionSerializer(serializers.ModelSerializer):
    created_at = serializers.IntegerField(source='created_at_unix')
    type = serializers.CharField(source='get_type_display')

    class Meta:
        model = CreditTransaction
        fields = ('id', 'created_at', 'display', 'app_url', 'web_url', 'type')
