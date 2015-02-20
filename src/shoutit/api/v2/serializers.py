# -*- coding: utf-8 -*-
"""

"""
from __future__ import unicode_literals
from collections import OrderedDict
import os

from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from shoutit.models import User, Video
from shoutit.utils import cloud_upload_image, random_uuid_str


class LocationSerializer(serializers.Serializer):
    country = serializers.CharField(min_length=2, max_length=2)
    city = serializers.CharField(max_length=200)
    latitude = serializers.FloatField()
    longitude = serializers.FloatField()


class VideoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Video
        fields = ('url', 'thumbnail_url', 'provider', 'id_on_provider', 'duration')


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'api_url', 'username', 'name', 'first_name', 'last_name', 'web_url', 'is_active')


class UserDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'api_url', 'username', 'name', 'first_name', 'last_name',
                  'web_url', 'is_active', 'image', 'sex', 'video', 'date_joined',
                  'bio', 'location', 'email', 'social_channels', 'push_tokens', 'image_file',
        )

    date_joined = serializers.IntegerField(source='created_at_unix')
    image = serializers.URLField(source='profile.image')
    sex = serializers.BooleanField(source='profile.Sex')
    bio = serializers.CharField(source='profile.Bio')
    video = VideoSerializer(source='profile.video', required=False)
    location = LocationSerializer()
    image_file = serializers.ImageField(required=False)

    def to_representation(self, instance):
        ret = super(UserDetailSerializer, self).to_representation(instance)

        # hide sensitive attributes from other users than owner
        if self.context['request'].user != instance:
            del ret['email']
            del ret['location']['latitude']
            del ret['location']['longitude']
            del ret['push_tokens']
            del ret['social_channels']

        return ret

    def to_internal_value(self, data):
        validated_data = super(UserDetailSerializer, self).to_internal_value(data)

        # todo: simplify, handle upload errors better
        image_file = validated_data.pop('image_file', None)
        if image_file:
            filename = image_file.name
            filename = random_uuid_str() + os.path.splitext(filename)[1]
            cloud_image = cloud_upload_image(image_file, 'user_image', filename, is_raw=False)

            if cloud_image:
                validated_data.pop('image_file', None)
                profile_data = validated_data.pop('profile', OrderedDict())
                profile_data.pop('image', None)
                profile_data['image'] = cloud_image.container.cdn_uri + '/' + cloud_image.name
                validated_data['profile'] = profile_data
            else:
                raise ValidationError({'image_file': "could not upload this file"})

        return validated_data

    def update(self, user, validated_data):
        profile_data = validated_data.pop('profile', None)
        profile = user.profile

        user.username = validated_data.get('username', user.username)
        user.first_name = validated_data.get('first_name', user.first_name)
        user.last_name = validated_data.get('last_name', user.last_name)
        user.email = validated_data.get('email', user.email)
        user.save()

        if profile_data:
            profile.Bio = profile_data.get('Bio', profile.Bio)
            profile.Sex = profile_data.get('Sex', profile.Sex)
            profile.image = profile_data.get('image', profile.image)
            profile.save()

        return user


