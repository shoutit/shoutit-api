# -*- coding: utf-8 -*-
"""

"""
from __future__ import unicode_literals
from collections import OrderedDict
import os
from push_notifications.models import APNSDevice, GCMDevice

from rest_framework import serializers, pagination
from rest_framework.exceptions import ValidationError
from rest_framework.pagination import DefaultObjectSerializer
from rest_framework.templatetags.rest_framework import replace_query_param
from common.constants import MessageAttachmentType, MESSAGE_ATTACHMENT_TYPE_SHOUT, MESSAGE_ATTACHMENT_TYPE_LOCATION, \
    CONVERSATION_TYPE_ABOUT_SHOUT, CONVERSATION_TYPE_CHAT
from common.utils import date_unix
from shoutit.controllers import shout_controller

from shoutit.models import User, Video, Tag, Trade, Conversation2, MessageAttachment, Message2
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
    name = serializers.CharField(max_length=30)
    is_listening = serializers.SerializerMethodField()

    class Meta:
        model = Tag
        fields = ('id', 'name', 'api_url', 'web_url', 'is_listening', 'listeners_count')

    def get_is_listening(self, tag):
        return tag.is_listening(self.root.context['request'].user)


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'api_url', 'web_url', 'username', 'name', 'first_name', 'last_name', 'is_active')


class TradeSerializer(serializers.ModelSerializer):
    type = serializers.CharField(source='type_name')
    title = serializers.CharField(source='item.name')
    price = serializers.FloatField(source='item.Price')
    currency = serializers.CharField(source='item.Currency.Code')
    images = serializers.ListField(source='item.images.all', child=serializers.URLField(), required=False)
    videos = VideoSerializer(source='item.videos.all', many=True, required=False)
    tags = TagSerializer(many=True)
    location = LocationSerializer()
    user = UserSerializer(read_only=True)
    date_published = serializers.SerializerMethodField()

    class Meta:
        model = Trade
        fields = ('id', 'api_url', 'web_url', 'type', 'title', 'text', 'price', 'currency', 'thumbnail',
                  'images', 'videos', 'tags', 'location', 'user', 'date_published',
        )

    def get_date_published(self, trade):
        return date_unix(trade.date_published)

    def to_internal_value(self, data):
        validated_data = super(TradeSerializer, self).to_internal_value(data)

        return validated_data

    def create(self, validated_data):
        location_data = validated_data.get('location')

        if validated_data['type_name'] == 'offer':
            shout = shout_controller.post_offer(name=validated_data['item']['name'],
                                                text=validated_data['text'],
                                                price=validated_data['item']['Price'],
                                                latitude=location_data['latitude'],
                                                longitude=location_data['longitude'],
                                                tags=validated_data['tags'],
                                                shouter=self.root.context['request'].user,
                                                country=location_data['country'],
                                                city=location_data['city'],
                                                address=location_data.get('address', ""),
                                                currency=validated_data['item']['Currency']['Code'],
                                                images=validated_data['item']['images']['all'],
                                                videos=validated_data['item']['videos']['all'])
        else:
            shout = shout_controller.post_request(name=validated_data['item']['name'],
                                                  text=validated_data['text'],
                                                  price=validated_data['item']['Price'],
                                                  latitude=location_data['latitude'],
                                                  longitude=location_data['longitude'],
                                                  tags=validated_data['tags'],
                                                  shouter=self.root.context['request'].user,
                                                  country=location_data['country'],
                                                  city=location_data['city'],
                                                  address=location_data.get('address', ""),
                                                  currency=validated_data['item']['Currency']['Code'],
                                                  images=validated_data['item']['images']['all'],
                                                  videos=validated_data['item']['videos']['all'])

        return shout


class UserDetailSerializer(serializers.ModelSerializer):
    date_joined = serializers.IntegerField(source='created_at_unix')
    image = serializers.URLField(source='profile.image')
    sex = serializers.BooleanField(source='profile.Sex')
    bio = serializers.CharField(source='profile.Bio')
    video = VideoSerializer(source='profile.video', required=False, allow_null=True)
    location = LocationSerializer()
    push_tokens = PushTokensSerializer()
    image_file = serializers.ImageField(required=False)

    class Meta:
        model = User
        fields = ('id', 'api_url', 'web_url', 'username', 'name', 'first_name', 'last_name',
                  'is_active', 'image', 'sex', 'video', 'date_joined',
                  'bio', 'location', 'email', 'social_channels', 'push_tokens', 'image_file',
        )

    def to_representation(self, instance):
        ret = super(UserDetailSerializer, self).to_representation(instance)

        # hide sensitive attributes from other users than owner
        if self.root.context['request'].user != instance:
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

        has_location = 'location' in data
        if has_location and isinstance(location_data, OrderedDict):
            ls = LocationSerializer(data=location_data)
            if not ls.is_valid():
                errors['location'] = ls.errors

        has_video = 'video' in data
        if has_video and isinstance(video_data, OrderedDict):
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
            profile.country = location_data['country']
            profile.city = location_data['city']
            profile.latitude = location_data['latitude']
            profile.longitude = location_data['longitude']
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


class MessageAttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = MessageAttachment
        fields = ('type', 'attached_object')

    def to_representation(self, instance):
        if instance.type == MESSAGE_ATTACHMENT_TYPE_SHOUT:
            attached_object = TradeSerializer(instance.attached_object, context=self.root.context).data
        elif instance.type == MESSAGE_ATTACHMENT_TYPE_LOCATION:
            attached_object = LocationSerializer(instance.attached_object, context=self.root.context).data
        else:
            attached_object = None

        if attached_object:
            rep = {
                MessageAttachmentType.values[instance.type]: attached_object
            }
        else:
            raise AssertionError("attached_object is not shout or location")

        return rep


class MessageSerializer(serializers.ModelSerializer):
    user = UserSerializer()
    attachments = MessageAttachmentSerializer(many=True, source='attachments.all')

    class Meta:
        model = Message2
        fields = ('id', 'read_url', 'delete_url', 'user', 'message', 'attachments')

    def to_internal_value(self, data):
        validated_data = super(MessageSerializer, self).to_internal_value(data)
        if 'message' not in validated_data:
            validated_data['message'] = None
        if 'attachments' not in validated_data:
            validated_data['attachments'] = None
        return validated_data


class ConversationSerializer(serializers.ModelSerializer):
    users = UserSerializer(many=True, source='users.all')
    last_message = MessageSerializer()
    type = serializers.CharField(source='type_name')

    class Meta:
        model = Conversation2
        fields = ('id', 'api_url', 'web_url', 'type', 'users', 'last_message')

    def to_representation(self, instance):
        rep = super(ConversationSerializer, self).to_representation(instance)

        if instance.type == CONVERSATION_TYPE_ABOUT_SHOUT:
            shout = TradeSerializer(instance.attached_object, context=self.root.context).data
            rep['about'] = shout

        return rep
