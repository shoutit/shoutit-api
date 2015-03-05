# -*- coding: utf-8 -*-
"""

"""
from __future__ import unicode_literals
from collections import OrderedDict
import os
import uuid
from push_notifications.models import APNSDevice, GCMDevice

from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.reverse import reverse
from common.constants import MESSAGE_ATTACHMENT_TYPE_SHOUT, MESSAGE_ATTACHMENT_TYPE_LOCATION, CONVERSATION_TYPE_ABOUT_SHOUT, \
    NotificationType
from common.utils import date_unix
from shoutit.api.api_utils import build_absolute_uri

from shoutit.models import User, Video, Tag, Trade, Conversation2, MessageAttachment, Message2, SharedLocation, Notification, Category, \
    Currency
from shoutit.utils import cloud_upload_image, random_uuid_str
from shoutit.controllers import shout_controller


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

    class Meta:
        model = Tag
        fields = ('id', 'name', 'api_url')


class TagDetailSerializer(TagSerializer):
    is_listening = serializers.SerializerMethodField()
    listeners_url = serializers.SerializerMethodField()
    shouts_url = serializers.SerializerMethodField(help_text="URL to show shouts of this user")

    class Meta(TagSerializer.Meta):
        model = Tag
        parent_fields = TagSerializer.Meta.fields
        fields = parent_fields + ('web_url', 'listeners_count', 'listeners_url', 'is_listening', 'shouts_url')

    def get_is_listening(self, tag):
        if 'request' in self.root.context and self.root.context['request'].user.is_authenticated():
            return tag.is_listening(self.root.context['request'].user)
        return False

    def get_listeners_url(self, tag):
        return reverse('tag-listeners', kwargs={'name': tag.name}, request=self.context['request'])

    def get_shouts_url(self, tag):
        return reverse('tag-shouts', kwargs={'name': tag.name}, request=self.context['request'])


class UserSerializer(serializers.ModelSerializer):
    image = serializers.URLField(source='profile.image')

    class Meta:
        model = User
        fields = ('id', 'api_url', 'web_url', 'username', 'name', 'first_name', 'last_name', 'is_active', 'image')


class UserDetailSerializer(UserSerializer):
    email = serializers.EmailField(allow_blank=True, max_length=254, required=False, help_text="Only shown for owner")
    date_joined = serializers.IntegerField(source='created_at_unix', read_only=True)
    sex = serializers.BooleanField(source='profile.Sex')
    bio = serializers.CharField(source='profile.Bio')
    video = VideoSerializer(source='profile.video', required=False, allow_null=True)
    location = LocationSerializer(help_text="latitude and longitude are only shown for owner")
    push_tokens = PushTokensSerializer(help_text="Only shown for owner")
    social_channels = serializers.ReadOnlyField(help_text="only shown for owner")
    image_file = serializers.ImageField(required=False)
    is_listening = serializers.SerializerMethodField(help_text="Whether signed in user is listening to this user")
    is_listener = serializers.SerializerMethodField(help_text="Whether this user is one of the signed in user's listeners")
    listeners_count = serializers.IntegerField(source='profile.listeners_count', help_text="Number of Listeners to this user")
    listeners_url = serializers.SerializerMethodField(help_text="URL to get this user listeners")
    listening_count = serializers.DictField(read_only=True, child=serializers.IntegerField(), source='profile.listening_count',
                                            help_text="object specifying the number of user listening. It has 'users' and 'tags' attributes")
    listening_url = serializers.SerializerMethodField(
        help_text="URL to get the listening of this user. `type` query param is default to 'users' it could be 'users' or 'tags'")
    is_owner = serializers.SerializerMethodField(help_text="Whether the signed in user and this user are the same")
    shouts_url = serializers.SerializerMethodField(help_text="URL to show shouts of this user")
    message_url = serializers.SerializerMethodField(
        help_text="URL to message this user if is possible. This is the case when user is one of the signed in user's listeners")

    class Meta(UserSerializer.Meta):
        parent_fields = UserSerializer.Meta.fields
        fields = parent_fields + ('sex', 'video', 'date_joined', 'bio', 'location', 'email', 'social_channels', 'push_tokens', 'image_file',
                                  'is_listening', 'is_listener', 'shouts_url', 'listeners_count', 'listeners_url',
                                  'listening_count', 'listening_url', 'is_owner', 'message_url')

    def get_is_listening(self, user):
        if 'request' in self.root.context and self.root.context['request'].user.is_authenticated():
            return user.profile.is_listening(self.root.context['request'].user)
        return False

    def get_is_listener(self, user):
        if 'request' in self.root.context and self.root.context['request'].user.is_authenticated():
            return user.profile.is_listener(self.root.context['request'].user.profile.stream2)
        return False

    def get_shouts_url(self, user):
        return reverse('user-shouts', kwargs={'username': user.username}, request=self.context['request'])

    def get_listening_url(self, user):
        return reverse('user-listening', kwargs={'username': user.username}, request=self.context['request'])

    def get_listeners_url(self, user):
        return reverse('user-listeners', kwargs={'username': user.username}, request=self.context['request'])

    def get_is_owner(self, user):
        return self.root.context['request'].user == user

    def get_message_url(self, user):
        return reverse('user-message', kwargs={'username': user.id}, request=self.context['request'])

    def to_representation(self, instance):
        ret = super(UserDetailSerializer, self).to_representation(instance)

        # hide sensitive attributes from other users than owner
        if not ret['is_owner']:
            del ret['email']
            del ret['location']['latitude']
            del ret['location']['longitude']
            del ret['push_tokens']
            del ret['social_channels']
            if not ret['is_listener']:
                del ret['message_url']

        # hide obvious attributes if the user `is_owner`
        else:
            del ret['is_listening']
            del ret['is_listener']
            del ret['message_url']

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


class TradeSerializer(serializers.ModelSerializer):
    type = serializers.CharField(source='type_name')
    location = LocationSerializer()
    title = serializers.CharField(source='item.name')
    price = serializers.FloatField(source='item.Price')
    currency = serializers.CharField(source='item.Currency.code')
    date_published = serializers.SerializerMethodField()
    user = UserSerializer(read_only=True)
    tags = TagSerializer(many=True)

    class Meta:
        model = Trade
        fields = ('id', 'api_url', 'web_url', 'type', 'location', 'title', 'text', 'price', 'currency', 'thumbnail', 'user',
                  'date_published', 'tags')

    def get_date_published(self, trade):
        return date_unix(trade.date_published)

    def to_internal_value(self, data):
        ret = super(TradeSerializer, self).to_internal_value(data)

        trade_id = data.get('id', None)
        if trade_id:
            try:
                uuid.UUID(trade_id)
                ret['id'] = trade_id
            except:
                raise ValidationError("'%s' is not a valid id." % trade_id)
        return ret


class TradeDetailSerializer(TradeSerializer):
    images = serializers.ListField(source='item.images.all', child=serializers.URLField(), required=False)
    videos = VideoSerializer(source='item.videos.all', many=True, required=False)
    reply_url = serializers.SerializerMethodField(help_text="URL to reply to this shout if possible, not set for shout owner.")
    related_requests = TradeSerializer(many=True, required=False)
    related_offers = TradeSerializer(many=True, required=False)

    class Meta(TradeSerializer.Meta):
        parent_fields = TradeSerializer.Meta.fields
        fields = parent_fields + ('images', 'videos', 'reply_url', 'related_requests', 'related_offers')

    def get_reply_url(self, trade):
        return reverse('shout-reply', kwargs={'id': trade.id}, request=self.context['request'])

    def to_representation(self, instance):
        ret = super(TradeDetailSerializer, self).to_representation(instance)
        if self.root.context['request'].user == instance.owner:
            del ret['reply_url']
        return ret

    def create(self, validated_data):
        location_data = validated_data.get('location')
        images = validated_data['item'].get('images', {'all': []})['all']
        videos = validated_data['item'].get('videos', {'all': []})['all']

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
                                                currency=validated_data['item']['Currency']['code'],
                                                images=images,
                                                videos=videos)
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
                                                  currency=validated_data['item']['Currency']['code'],
                                                  images=images,
                                                  videos=videos)

        return shout


class SharedLocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = SharedLocation
        fields = ['latitude', 'longitude']


class MessageAttachmentSerializer(serializers.ModelSerializer):
    shout = TradeSerializer(required=False)
    location = SharedLocationSerializer(required=False)

    class Meta:
        model = MessageAttachment
        fields = ['shout', 'location']

    def to_representation(self, instance):
        ret = super(MessageAttachmentSerializer, self).to_representation(instance)

        if instance.type == MESSAGE_ATTACHMENT_TYPE_SHOUT:
            del ret['location']
        if instance.type == MESSAGE_ATTACHMENT_TYPE_LOCATION:
            del ret['shout']

        return ret


class MessageSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    created_at = serializers.IntegerField(source='created_at_unix', read_only=True)

    class Meta:
        model = Message2
        fields = ('id', 'created_at', 'user', 'text')


class MessageDetailSerializer(MessageSerializer):
    attachments = MessageAttachmentSerializer(many=True, required=False,
                                              help_text="List of either {'shout': {Shout}} or {'location': {SharedLocation}}")
    conversation_url = serializers.SerializerMethodField()

    class Meta(MessageSerializer.Meta):
        parent_fields = MessageSerializer.Meta.fields
        fields = parent_fields + ('attachments', 'conversation_url')

    def get_conversation_url(self, message):
        return build_absolute_uri(reverse('conversation-detail', kwargs={'id': message.conversation.id}))

    def to_internal_value(self, data):
        validated_data = super(MessageSerializer, self).to_internal_value(data)

        # todo: better validation
        errors = OrderedDict()
        if 'text' not in validated_data:
            validated_data['text'] = None
        else:
            if validated_data['text'] == "":
                errors['text'] = "text can not be empty"

        if 'attachments' not in validated_data:
            validated_data['attachments'] = None
        else:
            if isinstance(validated_data['attachments'], list) and len(validated_data['attachments']):

                for attachment in validated_data['attachments']:
                    if 'shout' not in attachment and 'location' not in attachment:
                        errors['attachments'] = "attachment should have either 'shout' or 'location'"
                        continue
                    if 'shout' in attachment:
                        if 'id' not in attachment['shout']:
                            errors['attachments'] = {'shout': "shout object should have 'id'"}
                        elif not Trade.objects.filter(id=attachment['shout']['id']).exists():
                            errors['attachments'] = {'shout': "shout with id '%s' does not exist" % attachment['shout']['id']}

                    if 'location' in attachment and ('latitude' not in attachment['location'] or 'longitude' not in attachment['location']):
                        errors['attachments'] = {'shout': "location object should have 'latitude' and 'longitude'"}
            else:
                errors['attachments'] = "'attachments' should be a non empty list"

        if not (validated_data['text'] or validated_data['attachments']):
            errors['error'] = "please provide 'text' or 'attachments'"

        if errors:
            raise ValidationError(errors)

        return validated_data


class ConversationSerializer(serializers.ModelSerializer):
    users = UserSerializer(many=True, source='contributors', help_text="List of users in this conversations")
    last_message = MessageSerializer(required=False)
    type = serializers.CharField(source='type_name', help_text="Either 'chat' or 'about_shout'")
    created_at = serializers.IntegerField(source='created_at_unix', read_only=True)
    modified_at = serializers.IntegerField(source='modified_at_unix', read_only=True)
    about = serializers.SerializerMethodField(help_text="Only set if the conversation of type 'about_shout'")
    unread_messages_count = serializers.SerializerMethodField(help_text="Number of unread messages in this conversation")
    messages_url = serializers.SerializerMethodField(help_text="URL to get the messages of this conversation")
    reply_url = serializers.SerializerMethodField(help_text="URL to reply in this conversation")

    class Meta:
        model = Conversation2
        fields = ('id', 'created_at', 'modified_at', 'api_url', 'web_url', 'type', 'messages_count', 'unread_messages_count', 'users',
                  'last_message', 'about', 'messages_url', 'reply_url')

    def get_about(self, instance):
        # todo: map types
        if instance.type == CONVERSATION_TYPE_ABOUT_SHOUT:
            return TradeSerializer(instance.attached_object, context=self.root.context).data
        return None

    def get_unread_messages_count(self, instance):
        return instance.unread_messages_count(self.context['request'].user)

    def get_messages_url(self, conversation):
        return reverse('conversation-messages', kwargs={'id': conversation.id}, request=self.context['request'])

    def get_reply_url(self, conversation):
        return reverse('conversation-reply', kwargs={'id': conversation.id}, request=self.context['request'])


class AttachedObjectSerializer(serializers.Serializer):
    user = UserSerializer(source='attached_user', required=False)
    message = MessageDetailSerializer(source='attached_message', required=False)

    def to_representation(self, attached_object):
        # create reference to the object inside itself with name based on its class
        # to be used for representation
        class_name = attached_object.__class__.__name__
        if class_name == 'User':
            setattr(attached_object, 'attached_user', attached_object)
        if class_name == 'Message2':
            setattr(attached_object, 'attached_message', attached_object)

        return super(AttachedObjectSerializer, self).to_representation(attached_object)


class NotificationSerializer(serializers.ModelSerializer):
    created_at = serializers.IntegerField(source='created_at_unix')
    type = serializers.SerializerMethodField(help_text="Currently, either 'listen' or 'message'")
    attached_object = AttachedObjectSerializer(
        help_text="Attached Object that contain either 'user' or 'message' objects depending on notification type")

    class Meta:
        model = Notification
        fields = ('id', 'type', 'created_at', 'is_read', 'attached_object')

    def get_type(self, notification):
        return NotificationType.values[notification.type]


class CategorySerializer(serializers.ModelSerializer):
    main_tag = TagSerializer()

    class Meta:
        model = Category
        fields = ('name', 'main_tag')


class CurrencySerializer(serializers.ModelSerializer):
    class Meta:
        model = Currency
        fields = ('code', 'country', 'name')