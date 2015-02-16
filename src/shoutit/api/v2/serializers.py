# -*- coding: utf-8 -*-
"""

"""
from __future__ import unicode_literals

from shoutit.models import User
from rest_framework import serializers


class UserSerializer2(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'url', 'username', 'email', 'groups')
        extra_kwargs = {
            'url': {'lookup_field': 'username'}
        }


class UserSerializer(serializers.Serializer):
    username = serializers.CharField(required=True, max_length=30, min_length=2)

    def create(self, validated_data):
        return User.objects.create(**validated_data)

    def update(self, instance, validated_data):
        validated_data.get('username', instance.username)
        instance.save()
        return instance
