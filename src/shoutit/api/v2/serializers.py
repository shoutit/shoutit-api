# -*- coding: utf-8 -*-
"""

"""
from __future__ import unicode_literals
from collections import OrderedDict
import os
from push_notifications.models import APNSDevice, GCMDevice

from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from common.utils import date_unix

from shoutit.models import User, Video, Tag, Trade
from shoutit.utils import cloud_upload_image, random_uuid_str


class LocationSerializer(serializers.Serializer):
    country = serializers.CharField(min_length=2, max_length=2)
    city = serializers.CharField(max_length=200)
    latitude = serializers.FloatField()
    longitude = serializers.FloatField()
    address = serializers.CharField(required=False)


class PushTokensSerializer(serializers.Serializer):
    apns = serializers.CharField(max_length=64, allow_null=True)
    gcm = serializers.CharField(allow_null=True)


class VideoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Video
        fields = ('url', 'thumbnail_url', 'provider', 'id_on_provider', 'duration')


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ('id', 'name', 'api_url', 'web_url', 'is_listening', 'listeners_count')

    name = serializers.CharField(source='Name')
    is_listening = serializers.SerializerMethodField()

    def get_is_listening(self, tag):
        return tag.is_listening(self.context['request'].user)


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'api_url', 'username', 'name', 'first_name', 'last_name', 'web_url', 'is_active')


class TradeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Trade
        fields = ('id', 'api_url', 'web_url', 'type', 'title', 'text', 'price', 'currency', 'thumbnail',
                  'images', 'videos', 'tags', 'location', 'user', 'date_published',
        )

    title = serializers.CharField(source='Item.Name')
    text = serializers.CharField(source='Text')
    price = serializers.FloatField(source='Item.Price')
    currency = serializers.CharField(source='Item.Currency.Code')
    images = serializers.ListField(source='Item.get_image_urls', child=serializers.URLField())
    videos = VideoSerializer(source='Item.get_videos', many=True)
    tags = TagSerializer(many=True)
    location = LocationSerializer()
    user = UserSerializer()
    date_published = serializers.SerializerMethodField()

    def get_date_published(self, trade):
        return date_unix(trade.DatePublished)



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
    video = VideoSerializer(source='profile.video', required=False, allow_null=True)
    location = LocationSerializer()
    push_tokens = PushTokensSerializer()
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

        # force partial=false validation for location and video

        location_data = validated_data.get('location', {})
        profile_data = validated_data.get('profile', {})
        video_data = profile_data.get('video', {})

        errors = OrderedDict()

        if isinstance(location_data, OrderedDict):
            ls = LocationSerializer(data=location_data)
            if not ls.is_valid():
                errors['location'] = ls.errors

        if isinstance(video_data, OrderedDict):
            vs = VideoSerializer(data=video_data)
            if not vs.is_valid():
                errors['video'] = vs.errors

        if errors:
            raise ValidationError(errors)

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
        location_data = validated_data.get('location', {})
        push_tokens_data = validated_data.get('push_tokens', {})
        profile_data = validated_data.get('profile', {})
        video_data = profile_data.get('video', {})

        profile = user.profile

        user.username = validated_data.get('username', user.username)
        user.first_name = validated_data.get('first_name', user.first_name)
        user.last_name = validated_data.get('last_name', user.last_name)
        user.email = validated_data.get('email', user.email)
        user.save()

        if location_data:
            profile.Country = location_data['country']
            profile.City = location_data['city']
            profile.Latitude = location_data['latitude']
            profile.Longitude = location_data['longitude']
            profile.save()

        if profile_data:

            if video_data:
                video = Video(url=video_data['url'], thumbnail_url=video_data['thumbnail_url'], provider=video_data['provider'],
                              id_on_provider=video_data['id_on_provider'], duration=video_data['duration'])
                video.save()
                # delete existing video first
                if profile.video:
                    profile.video.delete()
                profile.video = video

            # if video sent as null, delete existing video
            elif video_data is None and profile.video:
                profile.video.delete()
                profile.video = None

            profile.Bio = profile_data.get('Bio', profile.Bio)
            profile.Sex = profile_data.get('Sex', profile.Sex)
            profile.image = profile_data.get('image', profile.image)
            profile.save()

        if push_tokens_data:
            if 'apns' in push_tokens_data:
                apns_token = push_tokens_data.get('apns')
                # delete user device if exists
                if user.apns_device:
                    user.delete_apns_device()
                if apns_token is not None:
                    # delete devices with same apns_token
                    APNSDevice.objects.filter(registration_id=apns_token).delete()
                    # create new device for user with apns_token
                    APNSDevice(registration_id=apns_token, user=user).save()

            if 'gcm' in push_tokens_data:
                gcm_token = push_tokens_data.get('gcm')
                # delete user device if exists
                if user.gcm_device:
                    user.delete_gcm_device()
                if gcm_token is not None:
                    # delete devices with same gcm_token
                    GCMDevice.objects.filter(registration_id=gcm_token).delete()
                    # create new device for user with gcm_token
                    GCMDevice(registration_id=gcm_token, user=user).save()

        return user


