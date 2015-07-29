# -*- coding: utf-8 -*-
"""

"""
from __future__ import unicode_literals
from collections import OrderedDict
import uuid
from django.contrib.auth import login
from django.contrib.auth.models import AnonymousUser
from django.db.models import Q
from ipware.ip import get_ip
from push_notifications.models import APNSDevice, GCMDevice

from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.fields import empty
from rest_framework.reverse import reverse
from common.constants import (
    MESSAGE_ATTACHMENT_TYPE_SHOUT, MESSAGE_ATTACHMENT_TYPE_LOCATION, CONVERSATION_TYPE_ABOUT_SHOUT,
    ReportType, REPORT_TYPE_USER, REPORT_TYPE_SHOUT, TOKEN_TYPE_RESET_PASSWORD, POST_TYPE_REQUEST,
    POST_TYPE_OFFER, MESSAGE_ATTACHMENT_TYPE_MEDIA)
from common.utils import any_in
from shoutit.controllers.facebook_controller import user_from_facebook_auth_response
from shoutit.controllers.gplus_controller import user_from_gplus_code
from shoutit.controllers.user_controller import update_profile_location
from shoutit.models import (
    User, Video, Tag, Shout, Conversation, MessageAttachment, Message, SharedLocation, Notification,
    Category, Currency, Report, PredefinedCity, ConfirmToken, FeaturedTag, DBCLConversation, SMSInvitation)
from shoutit.controllers import shout_controller, user_controller
from shoutit.utils import location_from_google_geocode_response


class LocationSerializer(serializers.Serializer):
    latitude = serializers.FloatField(min_value=-90, max_value=90, required=False)
    longitude = serializers.FloatField(min_value=-180, max_value=180, required=False)
    country = serializers.CharField(min_length=2, max_length=2, required=False, allow_blank=True)
    postal_code = serializers.CharField(max_length=10, required=False, allow_blank=True)
    state = serializers.CharField(max_length=50, required=False, allow_blank=True)
    city = serializers.CharField(max_length=100, required=False, allow_blank=True)
    address = serializers.CharField(max_length=200, required=False, allow_blank=True)

    google_geocode_response = serializers.DictField(required=False, allow_null=True)

    def to_internal_value(self, data):
        validated_data = super(LocationSerializer, self).to_internal_value(data)
        lat = 'latitude' in validated_data
        lng = 'longitude' in validated_data
        ggr = 'google_geocode_response' in validated_data
        if not ((lat and lng) or ggr):
            raise ValidationError({'error': "Could not find [latitude and longitude] or [google_geocode_response]"})

        google_geocode_response = validated_data.pop('google_geocode_response', None)
        if google_geocode_response:
            try:
                location = location_from_google_geocode_response(google_geocode_response)
            except (IndexError, KeyError, ValueError):
                raise ValidationError({'google_geocode_response': "Malformed Google geocode response"})
            validated_data.update(location)
        return validated_data


class PushTokensSerializer(serializers.Serializer):
    apns = serializers.CharField(max_length=64, allow_null=True)
    gcm = serializers.CharField(allow_null=True)


class VideoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Video
        fields = ('url', 'thumbnail_url', 'provider', 'id_on_provider', 'duration')


class TagSerializer(serializers.ModelSerializer):
    name = serializers.CharField(max_length=30)
    api_url = serializers.SerializerMethodField()

    class Meta:
        model = Tag
        fields = ('id', 'name', 'api_url', 'image')

    def get_api_url(self, tag):
        return reverse('tag-detail', kwargs={'name': tag.name}, request=self.context['request'])


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


class FeaturedTagSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source='tag.name')
    api_url = serializers.SerializerMethodField()
    image = serializers.URLField(source='tag.image')

    class Meta:
        model = FeaturedTag
        fields = ('id', 'title', 'name', 'api_url', 'image', 'rank')

    def get_api_url(self, f_tag):
        return reverse('tag-detail', kwargs={'name': f_tag.tag.name},
                       request=self.context['request'])


class CategorySerializer(serializers.ModelSerializer):
    name = serializers.CharField()
    main_tag = TagSerializer(read_only=True)

    class Meta:
        model = Category
        fields = ('name', 'main_tag')

    def to_internal_value(self, data):
        super(CategorySerializer, self).to_internal_value(data)
        return self.instance

    def validate_name(self, value):
        try:
            self.instance = Category.objects.get(name=value)
        except (Category.DoesNotExist, AttributeError):
            raise ValidationError(["Category %s does not exist" % value])


class UserSerializer(serializers.ModelSerializer):
    image = serializers.URLField(source='profile.image', required=False)
    api_url = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('id', 'api_url', 'web_url', 'username', 'name', 'first_name', 'last_name', 'is_activated', 'image')

    def __init__(self, instance=None, data=empty, **kwargs):
        super(UserSerializer, self).__init__(instance, data, **kwargs)
        self.fields['username'].required = False

    def get_api_url(self, user):
        return reverse('user-detail', kwargs={'username': user.username}, request=self.context['request'])

    def to_internal_value(self, data):
        ret = super(UserSerializer, self).to_internal_value(data)

        # validate the id only when sharing the user as an attached object
        if not isinstance(self.parent, AttachedObjectSerializer):
            return ret

        # todo: refactor
        user_id = data.get('id')
        if user_id == '':
            raise ValidationError({'id': 'This field can not be empty.'})
        if user_id:
            try:
                uuid.UUID(user_id)
                if not User.objects.filter(id=user_id).exists():
                    raise ValidationError("user with id '{}' does not exist".format(user_id))
                ret['id'] = user_id
            except (ValueError, TypeError):
                raise ValidationError({'id': "'%s' is not a valid id." % user_id})
        else:
            raise ValidationError({'id': "This field is required."})

        return ret


class UserDetailSerializer(UserSerializer):
    email = serializers.EmailField(allow_blank=True, max_length=254, required=False,
                                   help_text="Only shown for owner")
    is_password_set = serializers.BooleanField(read_only=True)
    date_joined = serializers.IntegerField(source='created_at_unix', read_only=True)
    gender = serializers.CharField(source='profile.gender', required=False)
    bio = serializers.CharField(source='profile.bio', required=False)
    video = VideoSerializer(source='profile.video', required=False, allow_null=True)
    location = LocationSerializer(help_text="latitude and longitude are only shown for owner", required=False)
    push_tokens = PushTokensSerializer(help_text="Only shown for owner", required=False)
    linked_accounts = serializers.ReadOnlyField(help_text="only shown for owner")
    is_listening = serializers.SerializerMethodField(
        help_text="Whether signed in user is listening to this user")
    is_listener = serializers.SerializerMethodField(
        help_text="Whether this user is one of the signed in user's listeners")
    listeners_count = serializers.IntegerField(source='profile.listeners_count', required=False,
                                               help_text="Number of Listeners to this user")
    listeners_url = serializers.SerializerMethodField(help_text="URL to get this user listeners")
    listening_count = serializers.DictField(read_only=True, child=serializers.IntegerField(),
                                            source='profile.listening_count',
                                            help_text="object specifying the number of user listening. It has 'users' and 'tags' attributes")
    listening_url = serializers.SerializerMethodField(
        help_text="URL to get the listening of this user. `type` query param is default to 'users' it could be 'users' or 'tags'")
    is_owner = serializers.SerializerMethodField(
        help_text="Whether the signed in user and this user are the same")
    shouts_url = serializers.SerializerMethodField(help_text="URL to show shouts of this user")
    message_url = serializers.SerializerMethodField(
        help_text="URL to message this user if is possible. This is the case when user is one of the signed in user's listeners")

    class Meta(UserSerializer.Meta):
        parent_fields = UserSerializer.Meta.fields
        fields = parent_fields + ('gender', 'video', 'date_joined', 'bio', 'location', 'email',
                                  'linked_accounts', 'push_tokens', 'is_password_set',
                                  'is_listening', 'is_listener', 'shouts_url', 'listeners_count',
                                  'listeners_url',
                                  'listening_count', 'listening_url', 'is_owner', 'message_url')

    def get_is_listening(self, user):
        if 'request' in self.root.context and self.root.context['request'].user.is_authenticated():
            return user.profile.is_listening(self.root.context['request'].user)
        return False

    def get_is_listener(self, user):
        if 'request' in self.root.context and self.root.context['request'].user.is_authenticated():
            return user.profile.is_listener(self.root.context['request'].user.profile.stream)
        return False

    def get_shouts_url(self, user):
        return reverse('user-shouts', kwargs={'username': user.username},
                       request=self.context['request'])

    def get_listening_url(self, user):
        return reverse('user-listening', kwargs={'username': user.username},
                       request=self.context['request'])

    def get_listeners_url(self, user):
        return reverse('user-listeners', kwargs={'username': user.username},
                       request=self.context['request'])

    def get_is_owner(self, user):
        return self.root.context['request'].user == user

    def get_message_url(self, user):
        return reverse('user-message', kwargs={'username': user.username},
                       request=self.context['request'])

    def to_representation(self, instance):
        ret = super(UserDetailSerializer, self).to_representation(instance)

        # hide sensitive attributes from other users than owner
        if not ret['is_owner']:
            del ret['email']
            del ret['location']['latitude']
            del ret['location']['longitude']
            del ret['location']['address']
            del ret['push_tokens']
            del ret['linked_accounts']
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
            user_controller.update_profile_location(profile, location_data)

        if profile_data:

            if video_data:
                video = Video(url=video_data['url'], thumbnail_url=video_data['thumbnail_url'],
                              provider=video_data['provider'],
                              id_on_provider=video_data['id_on_provider'],
                              duration=video_data['duration'])
                video.save()
                # delete existing video first
                if profile.video:
                    profile.video.delete()
                profile.video = video

            # if video sent as null, delete existing video
            elif video_data is None and profile.video:
                profile.video.delete()
                profile.video = None

            profile.bio = profile_data.get('bio', profile.bio)
            profile.gender = profile_data.get('gender', profile.gender)
            profile.image = profile_data.get('image', profile.image)
            # todo: optimize
            profile.save(update_fields=['bio', 'gender', 'image', 'video'])

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


class ShoutSerializer(serializers.ModelSerializer):
    type = serializers.ChoiceField(source='type_name', choices=['offer', 'request'],
                                   help_text="'offer' or 'request'")
    location = LocationSerializer()
    title = serializers.CharField(source='item.name')
    text = serializers.CharField(min_length=10, max_length=1000)
    price = serializers.FloatField(source='item.price', allow_null=True)
    currency = serializers.CharField(source='item.currency_code', allow_null=True,
                                     help_text='Currency code taken from list of available currencies')
    date_published = serializers.IntegerField(source='date_published_unix', read_only=True)
    user = UserSerializer(read_only=True)
    category = CategorySerializer()
    tags = TagSerializer(many=True, source='tag_objects')
    api_url = serializers.SerializerMethodField()

    class Meta:
        model = Shout
        fields = ('id', 'api_url', 'web_url', 'type', 'location', 'title', 'text', 'price',
                  'currency', 'thumbnail', 'video_url', 'user', 'date_published', 'category', 'tags')

    def get_api_url(self, shout):
        return reverse('shout-detail', kwargs={'id': shout.id}, request=self.context['request'])

    def validate_currency(self, value):
        try:
            if not value:
                raise ValueError()
            return Currency.objects.get(code__iexact=value)
        except Currency.DoesNotExist:
            raise ValidationError({'currency': ['Invalid currency']})
        except ValueError:
            return None

    def to_internal_value(self, data):
        # validate the id only when sharing the shout as message attachment
        if isinstance(self.parent, (MessageAttachmentSerializer, AttachedObjectSerializer)):
            shout_id = data.get('id')
            if shout_id == '':
                raise ValidationError({'id': ['This field can not be empty.']})
            if shout_id:
                try:
                    uuid.UUID(shout_id)
                    if not Shout.objects.filter(id=shout_id).exists():
                        raise ValidationError({'id': ["shout with id '%s' does not exist" % shout_id]})
                    return {'id': shout_id}
                except (ValueError, TypeError):
                    raise ValidationError({'id': ["'%s' is not a valid id." % shout_id]})
            else:
                raise ValidationError({'id': ["This field is required."]})

        # todo: hack!
        if not data:
            data = {}
        try:
            category = data.get('category')
            if not category:
                data['category'] = {'name': 'Other'}
        except AttributeError:
            pass
        # optional price and currency
        price_is_none = data.get('price') is None
        currency_is_none = data.get('currency') is None
        if price_is_none != currency_is_none:
            raise ValidationError({'price': ["price and currency must be either both set or both null"]})
        ret = super(ShoutSerializer, self).to_internal_value(data)
        return ret


class ShoutDetailSerializer(ShoutSerializer):
    images = serializers.ListField(source='item.images', child=serializers.URLField(),
                                   required=False)
    videos = VideoSerializer(source='item.videos.all', many=True, required=False)
    reply_url = serializers.SerializerMethodField(
        help_text="URL to reply to this shout if possible, not set for shout owner.")
    related_requests = ShoutSerializer(many=True, read_only=True)
    related_offers = ShoutSerializer(many=True, read_only=True)
    conversations = serializers.SerializerMethodField()

    class Meta(ShoutSerializer.Meta):
        parent_fields = ShoutSerializer.Meta.fields
        fields = parent_fields + ('images', 'videos', 'reply_url', 'related_requests', 'related_offers', 'conversations')

    def get_reply_url(self, shout):
        return reverse('shout-reply', kwargs={'id': shout.id}, request=self.context['request'])

    def get_conversations(self, shout):
        user = self.root.context['request'].user
        if isinstance(user, AnonymousUser):
            return []
        conversations = shout.conversations.filter(users=user)
        return ConversationSerializer(conversations, many=True, context=self.root.context).data

    def to_representation(self, instance):
        ret = super(ShoutDetailSerializer, self).to_representation(instance)
        if self.root.context['request'].user == instance.owner:
            del ret['reply_url']
        return ret

    def create(self, validated_data):
        return self.perform_save(shout=None, validated_data=validated_data)

    def update(self, shout, validated_data):
        return self.perform_save(shout=shout, validated_data=validated_data)

    def perform_save(self, shout, validated_data):
        shout_type = POST_TYPE_OFFER if validated_data.get('type_name') == 'offer' else POST_TYPE_REQUEST
        text = validated_data.get('text')
        title = validated_data['item'].get('name')
        price = validated_data['item'].get('price')
        currency = validated_data['item'].get('currency_code')

        category = validated_data.get('category')
        tags = validated_data.get('tag_objects')

        location = validated_data.get('location')

        images = validated_data['item'].get('images', None)
        videos = validated_data['item'].get('videos', {'all': None})['all']

        if not shout:
            user = self.root.context['request'].user
            shout = shout_controller.create_shout(user=user, shout_type=shout_type, title=title, text=text,
                                                  price=price, currency=currency, category=category, tags=tags,
                                                  location=location, images=images, videos=videos)
        else:
            shout = shout_controller.edit_shout(shout, shout_type=shout_type, title=title, text=text, price=price,
                                                currency=currency, category=category, tags=tags,
                                                location=location, images=images, videos=videos)
        return shout


class SharedLocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = SharedLocation
        fields = ['latitude', 'longitude']


class MessageAttachmentSerializer(serializers.ModelSerializer):
    shout = ShoutSerializer(required=False)
    location = SharedLocationSerializer(required=False)
    images = serializers.ListField(child=serializers.URLField(), required=False)
    videos = VideoSerializer(many=True, required=False)

    class Meta:
        model = MessageAttachment
        fields = ['shout', 'location', 'images', 'videos']

    def to_representation(self, instance):
        ret = super(MessageAttachmentSerializer, self).to_representation(instance)
        if instance.type == MESSAGE_ATTACHMENT_TYPE_SHOUT:
            del ret['location']
            del ret['images']
            del ret['videos']
        if instance.type == MESSAGE_ATTACHMENT_TYPE_LOCATION:
            del ret['shout']
            del ret['images']
            del ret['videos']
        if instance.type == MESSAGE_ATTACHMENT_TYPE_MEDIA:
            del ret['location']
            del ret['shout']
        return ret


class MessageSerializer(serializers.ModelSerializer):
    conversation_id = serializers.UUIDField(read_only=True)
    user = UserSerializer(read_only=True, required=False)
    created_at = serializers.IntegerField(source='created_at_unix', read_only=True)
    attachments = MessageAttachmentSerializer(many=True, required=False,
                                              help_text="List of either {'shout': {Shout}} or {'location': {SharedLocation}}")
    is_read = serializers.SerializerMethodField()

    class Meta:
        model = Message
        fields = ('id', 'created_at', 'conversation_id', 'user', 'text', 'attachments', 'is_read')

    def get_is_read(self, message):
        if 'request' in self.root.context and self.root.context['request'].user.is_authenticated():
            return message.is_read(self.root.context['request'].user)
        return False

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
            if isinstance(validated_data['attachments'], list) and len(
                    validated_data['attachments']):

                for attachment in validated_data['attachments']:
                    if not any_in(['shout', 'location', 'images', 'videos'], attachment):
                        errors['attachments'] = "attachment should have at least a 'shout', 'location', 'images' or 'videos'"
                        continue
                    if 'shout' in attachment:
                        if 'id' not in attachment['shout']:
                            errors['attachments'] = {'shout': "shout object should have 'id'"}
                        elif not Shout.objects.filter(id=attachment['shout']['id']).exists():
                            errors['attachments'] = {'shout': "shout with id '%s' does not exist" % attachment['shout']['id']}

                    if 'location' in attachment and ('latitude' not in attachment['location'] or 'longitude' not in attachment['location']):
                        errors['attachments'] = {'location': "location object should have 'latitude' and 'longitude'"}
            else:
                errors['attachments'] = "'attachments' should be a non empty list"

        if not (validated_data['text'] or validated_data['attachments']):
            errors['error'] = "please provide 'text' or 'attachments'"

        if errors:
            raise ValidationError(errors)

        return validated_data

    def to_representation(self, instance):
        ret = super(MessageSerializer, self).to_representation(instance)
        request = self.root.context.get('request')
        if request and request.method == 'POST':
            data = getattr(request, 'data', {})
            client_id = data.get('client_id')
            if client_id:
                ret['client_id'] = request.data.get('client_id')
        return ret


class ConversationSerializer(serializers.ModelSerializer):
    users = UserSerializer(many=True, source='contributors',
                           help_text="List of users in this conversations")
    last_message = MessageSerializer(required=False)
    type = serializers.CharField(source='type_name', help_text="Either 'chat' or 'about_shout'")
    created_at = serializers.IntegerField(source='created_at_unix', read_only=True)
    modified_at = serializers.IntegerField(source='modified_at_unix', read_only=True)
    about = serializers.SerializerMethodField(
        help_text="Only set if the conversation of type 'about_shout'")
    unread_messages_count = serializers.SerializerMethodField(
        help_text="Number of unread messages in this conversation")
    messages_url = serializers.SerializerMethodField(
        help_text="URL to get the messages of this conversation")
    reply_url = serializers.SerializerMethodField(help_text="URL to reply in this conversation")

    class Meta:
        model = Conversation
        fields = ('id', 'created_at', 'modified_at', 'web_url', 'type', 'messages_count',
                  'unread_messages_count', 'users',
                  'last_message', 'about', 'messages_url', 'reply_url')

    def get_about(self, instance):
        # todo: map types
        if instance.type == CONVERSATION_TYPE_ABOUT_SHOUT:
            return ShoutSerializer(instance.attached_object, context=self.root.context).data
        return None

    def get_unread_messages_count(self, instance):
        return instance.unread_messages_count(self.context['request'].user)

    def get_messages_url(self, conversation):
        return reverse('conversation-messages', kwargs={'id': conversation.id},
                       request=self.context['request'])

    def get_reply_url(self, conversation):
        return reverse('conversation-reply', kwargs={'id': conversation.id},
                       request=self.context['request'])


class AttachedObjectSerializer(serializers.Serializer):
    user = UserSerializer(source='attached_user', required=False)
    message = MessageSerializer(source='attached_message', required=False)
    shout = ShoutSerializer(source='attached_shout', required=False)

    def to_representation(self, attached_object):
        # create reference to the object inside itself with name based on its class
        # to be used for representation
        class_name = attached_object.__class__.__name__
        if class_name == 'User':
            setattr(attached_object, 'attached_user', attached_object)
        if class_name == 'Profile':
            setattr(attached_object, 'attached_user', attached_object.user)
        if class_name == 'Message':
            setattr(attached_object, 'attached_message', attached_object)
        if class_name == 'Shout':
            setattr(attached_object, 'attached_shout', attached_object)

        return super(AttachedObjectSerializer, self).to_representation(attached_object)


class NotificationSerializer(serializers.ModelSerializer):
    created_at = serializers.IntegerField(source='created_at_unix')
    type = serializers.CharField(source='type_name',
                                 help_text="Currently, either 'listen' or 'message'")
    attached_object = AttachedObjectSerializer(
        help_text="Attached Object that contain either 'user' or 'message' objects depending on notification type")

    class Meta:
        model = Notification
        fields = ('id', 'type', 'created_at', 'is_read', 'attached_object')


class CurrencySerializer(serializers.ModelSerializer):
    class Meta:
        model = Currency
        fields = ('code', 'country', 'name')


class ReportSerializer(serializers.ModelSerializer):
    created_at = serializers.IntegerField(source='created_at_unix', read_only=True)
    type = serializers.CharField(source='type_name',
                                 help_text="Currently, either 'user' or 'shout'", read_only=True)
    user = UserSerializer(read_only=True)
    attached_object = AttachedObjectSerializer(
        help_text="Attached Object that contain either 'user' or 'shout' objects depending on report type")

    class Meta:
        model = Report
        fields = ('id', 'created_at', 'type', 'user', 'text', 'attached_object')

    def to_internal_value(self, data):
        validated_data = super(ReportSerializer, self).to_internal_value(data)

        errors = OrderedDict()
        if 'attached_object' in validated_data:
            attached_object = validated_data['attached_object']
            if not ('attached_user' in attached_object or 'attached_shout' in attached_object):
                errors['attached_object'] = "attached_object should have either 'user' or 'shout'"

            if 'attached_shout' in attached_object:
                validated_data['type'] = 'shout'

            if 'attached_user' in attached_object:
                validated_data['type'] = 'user'
        else:
            errors['attached_object'] = ["This field is required."]
        if errors:
            raise ValidationError(errors)

        return validated_data

    def create(self, validated_data):
        attached_object = None
        report_type = ReportType.texts[validated_data['type']]

        if report_type == REPORT_TYPE_USER:
            attached_object = User.objects.get(
                id=validated_data['attached_object']['attached_user']['id'])
        if report_type == REPORT_TYPE_SHOUT:
            attached_object = Shout.objects.get(
                id=validated_data['attached_object']['attached_shout']['id'])
        text = validated_data['text'] if 'text' in validated_data else None
        report = Report.objects.create(user=self.root.context['request'].user, text=text,
                                       attached_object=attached_object, type=report_type)
        return report


class FacebookAuthSerializer(serializers.Serializer):
    facebook_access_token = serializers.CharField(max_length=500)
    user = UserDetailSerializer(required=False)

    def to_internal_value(self, data):
        ret = super(FacebookAuthSerializer, self).to_internal_value(data)
        facebook_access_token = ret.get('facebook_access_token')
        initial_user = ret.get('user', {})
        initial_user['ip'] = get_ip(self.context.get('request'))
        user = user_from_facebook_auth_response(facebook_access_token, initial_user)
        self.instance = user
        return ret


class GplusAuthSerializer(serializers.Serializer):
    gplus_code = serializers.CharField(max_length=500)
    user = UserDetailSerializer(required=False)

    def to_internal_value(self, data):
        ret = super(GplusAuthSerializer, self).to_internal_value(data)
        gplus_code = ret.get('gplus_code')
        initial_user = ret.get('user', {})
        initial_user['ip'] = get_ip(self.context.get('request'))
        user = user_from_gplus_code(gplus_code, initial_user, data.get('client_name'))
        self.instance = user
        return ret


class ShoutitSignupSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=70)
    first_name = serializers.CharField(min_length=2, max_length=30, required=False)
    last_name = serializers.CharField(min_length=1, max_length=30, required=False)
    email = serializers.EmailField()
    password = serializers.CharField(min_length=6, max_length=30)
    user = UserDetailSerializer(required=False)

    def to_internal_value(self, data):
        if not data:
            data = {}
        name = data.get('name')
        names = name.split()
        if len(names) < 2:
            raise ValidationError({'name': ['Please enter your full name.']})
        data['first_name'] = " ".join(names[0:-1])
        data['last_name'] = names[-1]

        ret = super(ShoutitSignupSerializer, self).to_internal_value(data)
        return ret

    def validate_email(self, email):
        email = email.lower()
        if User.objects.filter(email=email).exists():
            raise ValidationError({'email': ['Email is already used by another user.']})
        return email

    def create(self, validated_data):
        initial_user = validated_data.get('user', {})
        initial_user['ip'] = get_ip(self.context.get('request'))
        user = user_controller.user_from_shoutit_signup_data(validated_data, initial_user)
        return user


class ShoutitSigninSerializer(serializers.Serializer):
    email = serializers.CharField()
    password = serializers.CharField()
    user = UserDetailSerializer(required=False)

    def to_internal_value(self, data):
        ret = super(ShoutitSigninSerializer, self).to_internal_value(data)
        email = ret.get('email').lower()
        password = ret.get('password')
        initial_user = ret.get('user', {})
        try:
            user = User.objects.get(Q(email=email) | Q(username=email))
        except User.DoesNotExist:
            raise ValidationError(
                {'email': ['The email or username you entered do not belong to any account.']})
        if not user.check_password(password):
            raise ValidationError({'password': ['The password you entered is incorrect.']})
        self.instance = user
        if initial_user and initial_user.get('location'):
            update_profile_location(user.profile, initial_user.get('location'))
        return ret


class ShoutitVerifyEmailSerializer(serializers.Serializer):
    email = serializers.EmailField(required=False)

    def validate_email(self, email):
        user = self.context.get('request').user
        email = email.lower()
        if User.objects.filter(email=email).exclude(id=user.id).exists():
            raise ValidationError({'email': ['Email is already used by another user.']})
        return email

    def to_internal_value(self, data):
        ret = super(ShoutitVerifyEmailSerializer, self).to_internal_value(data)
        user = self.context.get('request').user
        email = ret.get('email')
        if email:
            user.email = email.lower()
            user.save(update_fields=['email'])
        self.instance = user
        return ret


class ShoutitResetPasswordSerializer(serializers.Serializer):
    email = serializers.CharField()

    def to_internal_value(self, data):
        ret = super(ShoutitResetPasswordSerializer, self).to_internal_value(data)
        email = ret.get('email').lower()
        try:
            user = User.objects.get(Q(email=email) | Q(username=email))
        except User.DoesNotExist:
            raise ValidationError({'email': ['The email or username you entered do not belong to '
                                             'any account.']})
        self.instance = user
        return ret


class ShoutitChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField()
    new_password = serializers.CharField(min_length=6, max_length=30)
    new_password2 = serializers.CharField(min_length=6, max_length=30)

    def to_internal_value(self, data):
        if not data:
            data = {}
        user = self.context.get('request').user
        if not user.is_password_set:
            data['old_password'] = 'ANYTHING'
        ret = super(ShoutitChangePasswordSerializer, self).to_internal_value(data)
        new_password = ret.get('new_password')
        new_password2 = ret.get('new_password2')

        if new_password != new_password2:
            raise ValidationError({'new_password': ['New passwords did not match.']})

        user.set_password(new_password)
        user.save(update_fields=['password'])
        user.backend = 'django.contrib.auth.backends.ModelBackend'
        login(self.context.get('request'), user)
        return ret

    def validate_old_password(self, value):
        user = self.context.get('request').user
        if user.is_password_set:
            if not user.check_password(value):
                raise ValidationError(['Old password does not match.'])


class ShoutitSetPasswordSerializer(serializers.Serializer):
    reset_token = serializers.CharField()
    new_password = serializers.CharField(min_length=6, max_length=30)
    new_password2 = serializers.CharField(min_length=6, max_length=30)

    def to_internal_value(self, data):
        ret = super(ShoutitSetPasswordSerializer, self).to_internal_value(data)
        new_password = ret.get('new_password')
        new_password2 = ret.get('new_password2')
        if new_password != new_password2:
            raise ValidationError({'new_password': ['New passwords did not match.']})
        user = self.instance
        user.set_password(new_password)
        user.save(update_fields=['password'])
        user.backend = 'django.contrib.auth.backends.ModelBackend'
        login(self.context.get('request'), user)
        return ret

    def validate_reset_token(self, value):
        try:
            cf = ConfirmToken.objects.get(type=TOKEN_TYPE_RESET_PASSWORD, token=value,
                                          is_disabled=False)
            self.instance = cf.user
        except ConfirmToken.DoesNotExist:
            raise ValidationError(['Reset token is invalid.'])


class SMSCodeSerializer(serializers.Serializer):
    sms_code = serializers.CharField(max_length=10, min_length=6)

    def to_internal_value(self, data):
        ret = super(SMSCodeSerializer, self).to_internal_value(data)
        sms_code = ret.get('sms_code').upper()
        try:
            dbcl_conversation = DBCLConversation.objects.get(sms_code__iexact=sms_code)
            self.instance = dbcl_conversation.to_user
        except DBCLConversation.DoesNotExist:
            raise ValidationError({'sms_code': ["Invalid sms_code"]})
        return ret


class PredefinedCitySerializer(serializers.ModelSerializer):
    class Meta:
        model = PredefinedCity
        fields = ('id', 'country', 'postal_code', 'state', 'city', 'latitude', 'longitude')


class SMSInvitationSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    message = serializers.CharField(max_length=1000, required=False)
    title = serializers.CharField(max_length=1000, required=False, write_only=True)

    class Meta:
        model = SMSInvitation
        fields = ('id', 'user', 'message', 'title', 'mobile', 'status', 'country')

    def to_internal_value(self, data):
        ret = super(SMSInvitationSerializer, self).to_internal_value(data)
        title = ret.get('title', "")
        message = ret.get('message', "")
        if not message and title:
            message = title
        if message:
            ret['message'] = message[:160]
        ret.pop('title', None)
        return ret
