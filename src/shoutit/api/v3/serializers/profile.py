"""

"""
from __future__ import unicode_literals

import uuid
from collections import OrderedDict

from django.contrib.auth.models import AnonymousUser
from django.core.validators import URLValidator
from push_notifications.models import APNSDevice, GCMDevice
from rest_framework import serializers
from rest_framework.fields import empty
from rest_framework.reverse import reverse

from shoutit.controllers import message_controller, location_controller, notifications_controller
from shoutit.models import User, InactiveUser, Profile, Page, Video
from shoutit.utils import url_with_querystring, correct_mobile
from .base import VideoSerializer, LocationSerializer, PushTokensSerializer
from ..exceptions import ERROR_REASON


class ProfileSerializer(serializers.ModelSerializer):
    type = serializers.CharField(source='type_name_v3', help_text="'user' or 'page'", read_only=True)
    image = serializers.URLField(source='ap.image', required=False)
    cover = serializers.URLField(source='ap.cover', required=False)
    api_url = serializers.SerializerMethodField()
    is_listening = serializers.SerializerMethodField(help_text="Whether you are listening to this Profile")
    listeners_count = serializers.IntegerField(required=False, help_text="Number of profiles (users, pages) Listening to this Profile")
    is_owner = serializers.SerializerMethodField(help_text="Whether this profile is yours")

    class Meta:
        model = User
        fields = ('id', 'type', 'api_url', 'web_url', 'username', 'name', 'first_name', 'last_name', 'is_activated',
                  'image', 'cover', 'is_listening', 'listeners_count', 'is_owner')

    def __init__(self, instance=None, data=empty, **kwargs):
        super(ProfileSerializer, self).__init__(instance, data, **kwargs)
        self.fields['username'].required = False

    def get_api_url(self, user):
        request = self.root.context.get('request')
        if request:
            return reverse('profile-detail', kwargs={'username': user.username}, request=request)
        return "https://api.shoutit.com/v3/profiles/" + user.username

    def get_is_listening(self, tag):
        request = self.root.context.get('request')
        user = request and request.user
        return user and user.is_authenticated() and user.is_listening(tag)

    def get_is_owner(self, user):
        return self.root.context['request'].user == user

    def to_internal_value(self, data):
        from .notification import AttachedObjectSerializer
        ret = super(ProfileSerializer, self).to_internal_value(data)

        # validate the id only when sharing the user as an attached object
        if not isinstance(self.parent, AttachedObjectSerializer):
            return ret

        # todo: refactor
        user_id = data.get('id')
        if user_id == '':
            raise serializers.ValidationError({'id': 'This field can not be empty'})
        if user_id:
            try:
                uuid.UUID(user_id)
                if not User.objects.filter(id=user_id).exists():
                    raise serializers.ValidationError({'id': "Profile with id '%s' does not exist" % user_id})
                ret['id'] = user_id
            except (ValueError, TypeError):
                raise serializers.ValidationError({'id': "'%s' is not a valid id" % user_id})
        else:
            raise serializers.ValidationError({'id': ("This field is required", ERROR_REASON.REQUIRED)})

        return ret

    def to_representation(self, instance):
        if not instance.is_active:
            ret = InactiveUser().to_dict
        else:
            ret = super(ProfileSerializer, self).to_representation(instance)
        if not ret.get('image'):
            ret['image'] = None
        if not ret.get('cover'):
            ret['cover'] = None
        return ret


# Todo: create two subclasses UserSerializer/UserDetailSerializer and PageSerializer/PageDetailSerializer
class ProfileDetailSerializer(ProfileSerializer):
    email = serializers.EmailField(allow_blank=True, max_length=254, required=False,
                                   help_text="Only shown for owner")
    mobile = serializers.CharField(source='profile.mobile', min_length=4, max_length=20, allow_blank=True, default='')
    is_password_set = serializers.BooleanField(read_only=True)
    date_joined = serializers.IntegerField(source='created_at_unix', read_only=True)
    gender = serializers.CharField(source='profile.gender', required=False)
    bio = serializers.CharField(source='profile.bio', allow_blank=True, default='', max_length=150)
    about = serializers.CharField(source='page.about', allow_blank=True, default='', max_length=150)
    video = VideoSerializer(source='ap.video', required=False, allow_null=True)
    location = LocationSerializer(help_text="latitude and longitude are only shown for owner", required=False)
    website = serializers.CharField(source='ap.website', allow_blank=True, default='')
    push_tokens = PushTokensSerializer(help_text="Only shown for owner", required=False)
    linked_accounts = serializers.ReadOnlyField(help_text="only shown for owner")
    is_listener = serializers.SerializerMethodField(help_text="Whether this profile is listening you")
    listeners_url = serializers.SerializerMethodField(help_text="URL to get this profile listeners")
    listening_count = serializers.DictField(
        read_only=True, child=serializers.IntegerField(),
        help_text="object specifying the number of profile listening. It has 'users', 'pages' and 'tags' attributes")
    listening_url = serializers.SerializerMethodField(
        help_text="URL to get the listening of this profile. `type` query param is default to 'users' it could be 'users', 'pages' or 'tags'")
    shouts_url = serializers.SerializerMethodField(help_text="URL to show shouts of this profile")
    conversation = serializers.SerializerMethodField(help_text="Conversation with type `chat` between you and this profile if exists")
    chat_url = serializers.SerializerMethodField(
        help_text="URL to message this profile if it is possible. This is the case when the profile is one of your listeners or an existing previous conversation")
    pages = ProfileSerializer(source='pages.all', many=True, read_only=True)
    admins = ProfileSerializer(source='ap.admins.all', many=True, read_only=True)

    class Meta(ProfileSerializer.Meta):
        parent_fields = ProfileSerializer.Meta.fields
        fields = parent_fields + ('gender', 'video', 'date_joined', 'bio', 'about', 'location', 'email', 'mobile', 'website',
                                  'linked_accounts', 'push_tokens', 'is_password_set', 'is_listener', 'shouts_url',
                                  'listeners_url', 'listening_count', 'listening_url', 'conversation', 'chat_url',
                                  'pages', 'admins')

    def get_is_listener(self, user):
        request = self.root.context.get('request')
        signed_user = request and request.user
        return signed_user and signed_user.is_authenticated() and user.is_listening(signed_user)

    def get_shouts_url(self, user):
        shouts_url = reverse('shout-list', request=self.context['request'])
        return url_with_querystring(shouts_url, user=user.username)

    def get_listening_url(self, user):
        return reverse('profile-listening', kwargs={'username': user.username}, request=self.context['request'])

    def get_listeners_url(self, user):
        return reverse('profile-listeners', kwargs={'username': user.username}, request=self.context['request'])

    def get_chat_url(self, user):
        return reverse('profile-chat', kwargs={'username': user.username}, request=self.context['request'])

    def get_conversation(self, user):
        from .message import ConversationSerializer
        request_user = self.root.context['request'].user
        if isinstance(request_user, AnonymousUser) or request_user.id == user.id:
            return None
        conversation = message_controller.conversation_exist(users=[request_user, user])
        if not conversation:
            return None
        return ConversationSerializer(conversation, context=self.root.context).data

    def to_representation(self, instance):
        if not instance.is_active:
            return InactiveUser().to_dict
        ret = super(ProfileDetailSerializer, self).to_representation(instance)

        # hide sensitive attributes from other users than owner
        if not ret['is_owner']:
            del ret['email']
            del ret['mobile']
            del ret['location']['latitude']
            del ret['location']['longitude']
            del ret['location']['address']
            del ret['push_tokens']
            del ret['linked_accounts']
            if not ret['is_listener']:
                del ret['chat_url']

        # hide obvious attributes if the user `is_owner`
        else:
            del ret['is_listening']
            del ret['is_listener']
            del ret['conversation']
            del ret['chat_url']

        if not ret.get('image'):
            ret['image'] = None
        if not ret.get('cover'):
            ret['cover'] = None
        return ret

    def to_internal_value(self, data):
        validated_data = super(ProfileDetailSerializer, self).to_internal_value(data)

        # Force partial=false validation for video
        errors = OrderedDict()
        has_video = 'video' in data
        profile_data = validated_data.get('ap', {})
        video_data = profile_data.get('video', {})
        if has_video and isinstance(video_data, OrderedDict):
            vs = VideoSerializer(data=video_data)
            if not vs.is_valid():
                errors['video'] = vs.errors
        if errors:
            raise serializers.ValidationError(errors)

        return validated_data

    def validate_email(self, email):
        user = self.context['request'].user
        email = email.lower()
        if User.objects.filter(email=email).exclude(id=user.id).exists():
            raise serializers.ValidationError("Email is already used by another profile")
        return email

    def validate_website(self, website):
        website = website.lower()
        # If no URL scheme given, assume http://
        if website and '://' not in website:
            website = u'http://%s' % website
        if website:
            URLValidator()(website)
        return website

    def validate_mobile(self, mobile):
        mobile = mobile.lower()
        if mobile:
            user = self.context['request'].user
            mobile = correct_mobile(mobile, user.location['country'], raise_exception=True)
        return mobile

    def update(self, user, validated_data):
        user_update_fields = []
        ap = user.ap
        ap_update_fields = []

        # User
        # Username
        new_username = validated_data.get('username')
        if new_username and new_username != user.username:
            user.username = new_username
            user_update_fields.append('username')
        # First name
        new_first_name = validated_data.get('first_name')
        if new_first_name and new_first_name != user.first_name:
            user.first_name = new_first_name
            user_update_fields.append('first_name')
        # Last name
        new_last_name = validated_data.get('last_name')
        if new_last_name and new_last_name != user.last_name:
            user.last_name = new_last_name
            user_update_fields.append('last_name')
        # Email
        new_email = validated_data.get('email')
        if new_email and new_email != user.email:
            user.email = new_email
            user_update_fields.extend(['email', 'is_activated'])
        # Save
        user.notify = False
        user.save(update_fields=user_update_fields)

        # Location
        location_data = validated_data.get('location', {})
        if location_data:
            location_controller.update_profile_location(ap, location_data)

        # AP
        ap_data = validated_data.get('ap', {})
        profile_data = validated_data.get('profile', {})
        page_data = validated_data.get('page', {})

        if isinstance(ap, Profile):
            bio = profile_data.get('bio')
            if bio is not None:
                ap.bio = bio
                ap_update_fields.append('bio')
            gender = profile_data.get('gender')
            if gender is not None:
                ap.gender = gender
                ap_update_fields.append('gender')
            mobile = profile_data.get('mobile')
            if mobile is not None:
                ap.mobile = mobile
                ap_update_fields.append('mobile')
        elif isinstance(ap, Page):
            pass

        if ap_data:
            image = ap_data.get('image')
            if image:
                ap.image = image
                ap_update_fields.append('image')
            cover = ap_data.get('cover')
            if cover:
                ap.cover = cover
                ap_update_fields.append('cover')
            website = ap_data.get('website')
            if website is not None:
                ap.website = website
                ap_update_fields.append('website')

            video_data = ap_data.get('video', {})
            if video_data:
                video = Video.create(url=video_data['url'], thumbnail_url=video_data['thumbnail_url'],
                                     provider=video_data['provider'], id_on_provider=video_data['id_on_provider'],
                                     duration=video_data['duration'])
                # # delete existing video first
                # if ap.video:
                #     ap.video.delete()
                ap.video = video
                ap_update_fields.append('video')

            # if video sent as null, delete existing video
            elif video_data is None and ap.video:
                # ap.video.delete()
                ap.video = None
                ap_update_fields.append('video')

        if ap_data or profile_data or page_data:
            ap.notify = False
            ap.save(update_fields=ap_update_fields)

        # Push Tokens
        push_tokens_data = validated_data.get('push_tokens', {})
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

        # Notify about updates
        notifications_controller.notify_user_of_user_update(user)
        return user


class GuestSerializer(ProfileSerializer):
    location = LocationSerializer(help_text="latitude and longitude are only shown for owner", required=False)
    push_tokens = PushTokensSerializer(required=False)
    date_joined = serializers.IntegerField(source='created_at_unix', read_only=True)

    class Meta(ProfileSerializer.Meta):
        fields = ('id', 'type', 'api_url', 'username', 'is_guest', 'date_joined', 'location', 'push_tokens')

    def to_representation(self, instance):
        ret = super(ProfileSerializer, self).to_representation(instance)
        return ret

    def update(self, user, validated_data):
        ap = user.ap

        # Location
        location_data = validated_data.get('location', {})
        if location_data:
            location_controller.update_profile_location(ap, location_data)

        # Push Tokens
        push_tokens_data = validated_data.get('push_tokens', {})
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

        # Notify about updates
        notifications_controller.notify_user_of_user_update(user)
        return user
