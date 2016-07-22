# -*- coding: utf-8 -*-
"""

"""
from __future__ import unicode_literals

import random
import uuid
from collections import OrderedDict

from django.conf import settings
from django.contrib.auth import login
from django.contrib.auth.models import AnonymousUser
from django.db.models import Q
from ipware.ip import get_real_ip
from rest_framework import serializers
from rest_framework.exceptions import ValidationError, AuthenticationFailed
from rest_framework.fields import empty
from rest_framework.reverse import reverse
from rest_framework.settings import api_settings

from common.constants import (
    MESSAGE_ATTACHMENT_TYPE_SHOUT, MESSAGE_ATTACHMENT_TYPE_LOCATION, CONVERSATION_TYPE_ABOUT_SHOUT,
    REPORT_TYPE_PROFILE, REPORT_TYPE_SHOUT, TOKEN_TYPE_RESET_PASSWORD, POST_TYPE_REQUEST,
    POST_TYPE_OFFER, MESSAGE_ATTACHMENT_TYPE_MEDIA, ConversationType, DEFAULT_CURRENCY_CODE)
from common.utils import any_in
from shoutit.controllers import (location_controller, shout_controller, user_controller, message_controller,
                                 media_controller)
from shoutit.controllers.facebook_controller import user_from_facebook_auth_response
from shoutit.controllers.gplus_controller import user_from_gplus_code
from shoutit.models import (
    User, Video, Tag, Shout, Conversation, MessageAttachment, Message, SharedLocation, Notification, Category,
    Currency, Report, PredefinedCity, ConfirmToken, FeaturedTag, DBCLConversation, SMSInvitation, DiscoverItem,
    Profile, Page)
from shoutit.models.auth import InactiveUser
from shoutit.models.post import InactiveShout
from shoutit.utils import generate_username, debug_logger, url_with_querystring


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
        google_geocode_response = validated_data.pop('google_geocode_response', None)
        address = validated_data.pop('address', None)
        request = self.root.context.get('request')
        ip = get_real_ip(request) if request else None

        if lat and lng:
            # Get location attributes using latitude, longitude or IP
            location = location_controller.from_location_index(validated_data.get('latitude'),
                                                               validated_data.get('longitude'), ip)
        # Todo: Deprecate
        elif ggr:
            # Handle Google geocode response if provided
            try:
                location = location_controller.parse_google_geocode_response(google_geocode_response)
            except (IndexError, KeyError, ValueError):
                raise ValidationError({'google_geocode_response': "Malformed Google geocode response"})
        elif ip:
            # Get location attributes using IP
            location = location_controller.from_ip(ip, use_location_index=True)
        elif address and request and request.user.is_authenticated():
            # Update the logged in user address
            location = request.user.location
        else:
            raise ValidationError({
                'non_field_errors': "Could not find [latitude and longitude] or [google_geocode_response] or figure the IP Address"})

        if address:
            location.update({'address': address})
        validated_data.update(location)
        return validated_data


class PushTokensSerializer(serializers.Serializer):
    apns = serializers.CharField(max_length=64, allow_null=True)
    gcm = serializers.CharField(allow_null=True)


class VideoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Video
        fields = ('url', 'thumbnail_url', 'provider', 'id_on_provider', 'duration')


class DiscoverItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = DiscoverItem
        fields = ('id', 'api_url', 'title', 'subtitle', 'position', 'image', 'icon')
        extra_kwargs = {api_settings.URL_FIELD_NAME: {'view_name': 'discover-detail'}}

    def to_representation(self, instance):
        ret = super(DiscoverItemSerializer, self).to_representation(instance)
        if not ret.get('image'):
            ret['image'] = ""
        if not ret.get('cover'):
            ret['cover'] = ""
        if not ret.get('icon'):
            ret['icon'] = ""
        return ret


class DiscoverItemDetailSerializer(serializers.ModelSerializer):
    shouts_url = serializers.SerializerMethodField()
    parents = DiscoverItemSerializer(many=True)
    children = DiscoverItemSerializer(many=True)

    class Meta(DiscoverItemSerializer.Meta):
        model = DiscoverItem
        parent_fields = DiscoverItemSerializer.Meta.fields
        fields = parent_fields + (
            'description', 'cover', 'countries', 'parents', 'show_children', 'children', 'show_shouts', 'shouts_url'
        )

    def to_representation(self, instance):
        ret = super(DiscoverItemDetailSerializer, self).to_representation(instance)
        if not instance.show_shouts:
            ret.pop('shouts_url', None)
        if not ret.get('image'):
            ret['image'] = ""
        if not ret.get('cover'):
            ret['cover'] = ""
        if not ret.get('icon'):
            ret['icon'] = ""
        return ret

    def get_shouts_url(self, discover_item):
        shouts_url = reverse('shout-list', request=self.context['request'])
        return url_with_querystring(shouts_url, discover=discover_item.pk)


class TagSerializer(serializers.ModelSerializer):
    name = serializers.CharField(max_length=30)
    api_url = serializers.SerializerMethodField()

    class Meta:
        model = Tag
        fields = ('id', 'name', 'api_url', 'image')

    def to_internal_value(self, data):
        if isinstance(data, basestring):
            data = {'name': data}
        ret = super(TagSerializer, self).to_internal_value(data)
        return ret

    def get_api_url(self, tag):
        return reverse('tag-detail', kwargs={'name': tag.name}, request=self.context['request'])

    def to_representation(self, instance):
        ret = super(TagSerializer, self).to_representation(instance)
        if not ret.get('image'):
            ret['image'] = "https://tag-image.static.shoutit.com/default.jpg"
        return ret


class TagDetailSerializer(TagSerializer):
    is_listening = serializers.SerializerMethodField(help_text="Whether logged in user is listening to this tag")
    listeners_url = serializers.SerializerMethodField(help_text="URL to show listeners of this tag")
    shouts_url = serializers.SerializerMethodField(help_text="URL to show shouts with this tag")

    class Meta(TagSerializer.Meta):
        model = Tag
        parent_fields = TagSerializer.Meta.fields
        fields = parent_fields + ('web_url', 'listeners_count', 'listeners_url', 'is_listening', 'shouts_url')

    def get_is_listening(self, tag):
        request = self.root.context.get('request')
        user = request and request.user
        return user and user.is_authenticated() and user.is_listening(tag)

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
        return reverse('tag-detail', kwargs={'name': f_tag.tag.name}, request=self.context['request'])


class CategorySerializer(serializers.ModelSerializer):
    name = serializers.CharField()
    slug = serializers.CharField(read_only=True)
    main_tag = TagSerializer(read_only=True)

    class Meta:
        model = Category
        fields = ('name', 'slug', 'icon', 'image', 'main_tag')

    def to_internal_value(self, data):
        if isinstance(data, basestring):
            data = {'name': data}
        super(CategorySerializer, self).to_internal_value(data)
        return self.instance

    def validate_name(self, value):
        # Todo: HACK until new apps are released
        if value == "Jobs Wanted":
            value == "Jobs"
        try:
            self.instance = Category.objects.get(name=value)
        except (Category.DoesNotExist, AttributeError):
            raise ValidationError(["Category %s does not exist" % value])

    def to_representation(self, instance):
        ret = super(CategorySerializer, self).to_representation(instance)
        if not ret.get('image'):
            ret['image'] = ""
        if not ret.get('icon'):
            ret['icon'] = ""
        return ret


class UserSerializer(serializers.ModelSerializer):
    type = serializers.CharField(source='get_type_display', help_text="'Profile' or 'Page'", read_only=True)
    image = serializers.URLField(source='ap.image', required=False)
    cover = serializers.URLField(source='ap.cover', required=False)
    api_url = serializers.SerializerMethodField()
    is_listening = serializers.SerializerMethodField(help_text="Whether signed in user is listening to this user")
    listeners_count = serializers.IntegerField(required=False, help_text="Number of Listeners to this user")

    class Meta:
        model = User
        fields = ('id', 'type', 'api_url', 'web_url', 'username', 'name', 'first_name', 'last_name', 'is_activated',
                  'image', 'cover', 'is_listening', 'listeners_count')

    def __init__(self, instance=None, data=empty, **kwargs):
        super(UserSerializer, self).__init__(instance, data, **kwargs)
        self.fields['username'].required = False

    def get_api_url(self, user):
        request = self.root.context.get('request')
        if request:
            return reverse('user-detail', kwargs={'username': user.username}, request=request)
        return "https://api.shoutit.com/v2/users/" + user.username

    def get_is_listening(self, tag):
        request = self.root.context.get('request')
        user = request and request.user
        return user and user.is_authenticated() and user.is_listening(tag)

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
                if not User.exists(id=user_id):
                    raise ValidationError("user with id '{}' does not exist".format(user_id))
                ret['id'] = user_id
            except (ValueError, TypeError):
                raise ValidationError({'id': "'%s' is not a valid id" % user_id})
        else:
            raise ValidationError({'id': "This field is required"})

        return ret

    def to_representation(self, instance):
        if not instance.is_active:
            ret = InactiveUser().to_dict
        else:
            ret = super(UserSerializer, self).to_representation(instance)
        if not ret.get('image'):
            ret['image'] = "https://user-image.static.shoutit.com/default_male.jpg"
        if not ret.get('cover'):
            ret['cover'] = ""
        return ret


class UserDetailSerializer(UserSerializer):
    email = serializers.EmailField(allow_blank=True, max_length=254, required=False,
                                   help_text="Only shown for owner")
    is_password_set = serializers.BooleanField(read_only=True)
    date_joined = serializers.IntegerField(source='created_at_unix', read_only=True)
    gender = serializers.CharField(source='profile.gender', required=False)
    bio = serializers.CharField(source='profile.bio', required=False, allow_blank=True)
    video = VideoSerializer(source='ap.video', required=False, allow_null=True)
    location = LocationSerializer(help_text="latitude and longitude are only shown for owner", required=False)
    website = serializers.URLField(source='ap.website', required=False)
    push_tokens = PushTokensSerializer(help_text="Only shown for owner", required=False)
    linked_accounts = serializers.ReadOnlyField(source='v2_linked_accounts', help_text="only shown for owner")
    is_listener = serializers.SerializerMethodField(help_text="Whether this user is listening to signed in user")
    listeners_url = serializers.SerializerMethodField(help_text="URL to get this user listeners")
    listening_count = serializers.DictField(
        read_only=True, child=serializers.IntegerField(),
        help_text="object specifying the number of user listening. It has 'users' and 'tags' attributes")
    listening_url = serializers.SerializerMethodField(
        help_text="URL to get the listening of this user. `type` query param is default to 'users' it could be 'users' or 'tags'")
    is_owner = serializers.SerializerMethodField(help_text="Whether the signed in user and this user are the same")
    shouts_url = serializers.SerializerMethodField(help_text="URL to show shouts of this user")
    message_url = serializers.SerializerMethodField(
        help_text="URL to message this user if is possible. This is the case when user is one of the signed in user's listeners")
    pages = UserSerializer(source='pages.all', many=True, read_only=True)
    admins = UserSerializer(source='ap.admins.all', many=True, read_only=True)

    class Meta(UserSerializer.Meta):
        parent_fields = UserSerializer.Meta.fields
        fields = parent_fields + ('gender', 'video', 'date_joined', 'bio', 'location', 'email', 'website',
                                  'linked_accounts', 'push_tokens', 'is_password_set', 'is_listener', 'shouts_url',
                                  'listeners_url', 'listening_count', 'listening_url', 'is_owner',
                                  'message_url', 'pages', 'admins')

    def get_is_listener(self, user):
        request = self.root.context.get('request')
        signed_user = request and request.user
        return signed_user and signed_user.is_authenticated() and user.is_listening(signed_user)

    def get_shouts_url(self, user):
        return reverse('user-shouts', kwargs={'username': user.username}, request=self.context['request'])

    def get_listening_url(self, user):
        return reverse('user-listening', kwargs={'username': user.username}, request=self.context['request'])

    def get_listeners_url(self, user):
        return reverse('user-listeners', kwargs={'username': user.username}, request=self.context['request'])

    def get_is_owner(self, user):
        return self.root.context['request'].user == user

    def get_message_url(self, user):
        return reverse('user-message', kwargs={'username': user.username}, request=self.context['request'])

    def to_representation(self, instance):
        if not instance.is_active:
            return InactiveUser().to_dict
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

        if not ret.get('image'):
            ret['image'] = "https://user-image.static.shoutit.com/default_male.jpg"
        if not ret.get('cover'):
            ret['cover'] = ""
        return ret

    def to_internal_value(self, data):
        validated_data = super(UserDetailSerializer, self).to_internal_value(data)

        # force partial=false validation for location and video
        profile_data = validated_data.get('profile', {})
        video_data = profile_data.get('video', {})

        errors = OrderedDict()

        has_video = 'video' in data
        if has_video and isinstance(video_data, OrderedDict):
            vs = VideoSerializer(data=video_data)
            if not vs.is_valid():
                errors['video'] = vs.errors

        if errors:
            raise ValidationError(errors)

        return validated_data

    def validate_email(self, email):
        user = self.context['request'].user
        email = email.lower()
        if User.objects.filter(email=email).exclude(id=user.id).exists():
            raise ValidationError(["Email is already used by another user"])
        return email

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
            if bio:
                ap.bio = bio
                ap_update_fields.append('bio')
            gender = profile_data.get('gender')
            if gender:
                ap.gender = gender
                ap_update_fields.append('gender')
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
            if website:
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
            user.update_push_tokens(push_tokens_data, 'v2')

        return user


class ShoutSerializer(serializers.ModelSerializer):
    type = serializers.ChoiceField(source='get_type_display', choices=['offer', 'request'],
                                   help_text="'offer' or 'request'")
    location = LocationSerializer()
    title = serializers.CharField(min_length=6, max_length=500, source='item.name')
    text = serializers.CharField(min_length=10, max_length=5000)
    price = serializers.FloatField(source='item.v2_price', allow_null=True)
    currency = serializers.CharField(source='item.currency_code', allow_null=True,
                                     help_text='Currency code taken from list of available currencies')
    date_published = serializers.IntegerField(source='published_at_unix', read_only=True)
    user = UserSerializer(read_only=True)
    category = CategorySerializer()
    tags = serializers.SerializerMethodField()
    api_url = serializers.SerializerMethodField()

    class Meta:
        model = Shout
        fields = ('id', 'api_url', 'web_url', 'type', 'location', 'title', 'text', 'price',
                  'currency', 'thumbnail', 'video_url', 'user', 'date_published', 'category', 'tags')

    def get_api_url(self, shout):
        return reverse('shout-detail', kwargs={'id': shout.id}, request=self.context['request'])

    def get_tags(self, shout):
        return []

    def validate_currency(self, value):
        try:
            if not value:
                raise ValueError()
            return Currency.objects.get(code__iexact=value)
        except Currency.DoesNotExist:
            raise ValidationError(['Invalid currency'])
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
                    if not Shout.exists(id=shout_id):
                        raise ValidationError({'id': ["shout with id '%s' does not exist" % shout_id]})
                    return {'id': shout_id}
                except (ValueError, TypeError):
                    raise ValidationError({'id': ["'%s' is not a valid id" % shout_id]})
            else:
                raise ValidationError({'id': ["This field is required"]})

        # todo: hack!
        if not data:
            data = {}
        try:
            category = data.get('category')
            if not (category and category.get('name')):
                data['category'] = {'name': 'Other'}
            if data['category'] == 'cv-video':  # fix for current ios bug
                data['category'] = {'name': 'Jobs Wanted'}
        except AttributeError:
            pass
        # optional price and currency
        price_is_none = data.get('price') is None
        currency_is_none = data.get('currency') is None
        if price_is_none != currency_is_none:
            raise ValidationError({'price': ["price and currency must be either both set or both null"]})
        ret = super(ShoutSerializer, self).to_internal_value(data)
        return ret

    def to_representation(self, instance):
        if instance.is_muted or instance.is_disabled:
            ret = InactiveShout().to_dict
        else:
            ret = super(ShoutSerializer, self).to_representation(instance)
        if 'currency' in ret and not ret['currency']:
            ret['currency'] = DEFAULT_CURRENCY_CODE
        return ret


class ShoutDetailSerializer(ShoutSerializer):
    images = serializers.ListField(source='item.images', child=serializers.URLField(), required=False)
    videos = VideoSerializer(source='item.videos.all', many=True, required=False)
    publish_to_facebook = serializers.BooleanField(write_only=True, required=False)
    reply_url = serializers.SerializerMethodField(
        help_text="URL to reply to this shout if possible, not set for shout owner")
    related_requests = serializers.SerializerMethodField()
    related_offers = serializers.SerializerMethodField()
    conversations = serializers.SerializerMethodField()

    class Meta(ShoutSerializer.Meta):
        parent_fields = ShoutSerializer.Meta.fields
        fields = parent_fields + ('images', 'videos', 'published_on', 'publish_to_facebook', 'reply_url',
                                  'related_requests', 'related_offers', 'conversations')

    def get_related_requests(self, shout):
        return []

    def get_related_offers(self, shout):
        return []

    def get_reply_url(self, shout):
        return reverse('shout-reply', kwargs={'id': shout.id}, request=self.context['request'])

    def get_conversations(self, shout):
        user = self.root.context['request'].user
        if isinstance(user, AnonymousUser):
            return []
        conversations = shout.conversations.filter(users=user)
        return ConversationSerializer(conversations, many=True, context=self.root.context).data

    def to_representation(self, instance):
        if instance.is_muted or instance.is_disabled:
            return InactiveShout().to_dict
        ret = super(ShoutDetailSerializer, self).to_representation(instance)
        if self.root.context['request'].user == instance.owner:
            del ret['reply_url']
        return ret

    def validate_images(self, images):
        valid_images = []
        for image in images[:settings.MAX_IMAGES_PER_ITEM]:
            if 'shout-image.static.shoutit.com' in image and '.jpg' in image:
                valid_images.append(image)
                continue
            try:
                s3_image = media_controller.upload_image_to_s3(
                    bucket_name='shoutit-shout-image-original', url=image,
                    public_url='https://shout-image.static.shoutit.com', raise_exception=True)
                valid_images.append(s3_image)
            except Exception as e:
                debug_logger.warn(str(e), exc_info=True)
        return valid_images

    def create(self, validated_data):
        return self.perform_save(shout=None, validated_data=validated_data)

    def update(self, shout, validated_data):
        return self.perform_save(shout=shout, validated_data=validated_data)

    def perform_save(self, shout, validated_data):
        shout_type_name = validated_data.get('get_type_display')
        shout_types = {
            'request': POST_TYPE_REQUEST,
            'offer': POST_TYPE_OFFER,
            None: None
        }
        shout_type = shout_types[shout_type_name]
        text = validated_data.get('text')
        item = validated_data.get('item', {})
        title = item.get('name')
        price = item.get('v2_price')
        if price:
            price = int(float(price) * 100)
        currency = item.get('currency_code')

        category = validated_data.get('category')

        location = validated_data.get('location')
        publish_to_facebook = validated_data.get('publish_to_facebook')

        images = item.get('images', None)
        videos = item.get('videos', {'all': None})['all']

        request = self.root.context.get('request')
        user = getattr(request, 'user', None) or self.root.context.get('user')
        page_admin_user = getattr(request, 'page_admin_user', None)

        if not shout:
            shout = shout_controller.create_shout_v2(
                user=user, shout_type=shout_type, title=title, text=text, price=price, currency=currency,
                category=category, location=location, images=images, videos=videos,
                page_admin_user=page_admin_user, publish_to_facebook=publish_to_facebook,
                api_client=getattr(request, 'api_client', None), api_version=request.version
            )
        else:
            shout = shout_controller.edit_shout_v2(
                shout, shout_type=shout_type, title=title, text=text, price=price, currency=currency, category=category,
                location=location, images=images, videos=videos, page_admin_user=page_admin_user
            )
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
        request = self.root.context.get('request')
        user = request and getattr(request, 'user', None)
        if user and user.is_authenticated():
            return message.is_read(user)
        return False

    def to_internal_value(self, data):
        validated_data = super(MessageSerializer, self).to_internal_value(data)
        attachments = validated_data.get('attachments')
        text = validated_data.get('text')
        errors = OrderedDict()

        if text is None and attachments == []:
            raise ValidationError({'error': "Provide 'text' or 'attachments'"})

        if attachments is not None:
            if isinstance(attachments, list) and len(attachments):
                for attachment in attachments:
                    if not any_in(['shout', 'location', 'images', 'videos'], attachment):
                        errors[
                            'attachments'] = "attachment should have at least a 'shout', 'location', 'images' or 'videos'"
                        continue
                    if 'shout' in attachment:
                        if 'id' not in attachment['shout']:
                            errors['attachments'] = {'shout': "shout object should have 'id'"}
                        elif not Shout.exists(id=attachment['shout']['id']):
                            errors['attachments'] = {
                                'shout': "shout with id '%s' does not exist" % attachment['shout']['id']}

                    if 'location' in attachment and (
                            'latitude' not in attachment['location'] or 'longitude' not in attachment['location']):
                        errors['attachments'] = {'location': "location object should have 'latitude' and 'longitude'"}
            else:
                errors['attachments'] = "'attachments' should be a non empty list"

        if text is not None and text == "" and attachments is None:
            errors['text'] = "text can not be empty"

        if attachments is None and text is None:
            errors['error'] = "Provide 'text' or 'attachments'"

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

    def create(self, validated_data):
        request = self.root.context.get('request')
        user = getattr(request, 'user', None)
        page_admin_user = getattr(request, 'page_admin_user', None)
        conversation = self.root.context.get('conversation')
        to_users = self.root.context.get('to_users')
        about = self.root.context.get('about')
        text = validated_data.get('text')
        attachments = validated_data.get('attachments')
        message = message_controller.send_message(conversation, user, to_users=to_users, about=about, text=text,
                                                  attachments=attachments, request=request,
                                                  page_admin_user=page_admin_user)
        return message


class ConversationSerializer(serializers.ModelSerializer):
    users = UserSerializer(many=True, source='contributors', help_text="List of users in this conversations",
                           read_only=True)
    last_message = MessageSerializer(required=False)
    type = serializers.ChoiceField(choices=ConversationType.texts, source='get_type_display',
                                   help_text="'chat', 'about_shout' or 'public_chat'")
    created_at = serializers.IntegerField(source='created_at_unix', read_only=True)
    modified_at = serializers.IntegerField(source='modified_at_unix', read_only=True)
    subject = serializers.CharField(max_length=25)
    about = serializers.SerializerMethodField(help_text="Only set if the conversation of type 'about_shout'")
    unread_messages_count = serializers.SerializerMethodField(
        help_text="Number of unread messages in this conversation")
    messages_url = serializers.SerializerMethodField(help_text="URL to get the messages of this conversation")
    reply_url = serializers.SerializerMethodField(help_text="URL to reply in this conversation")

    class Meta:
        model = Conversation
        fields = ('id', 'created_at', 'modified_at', 'web_url', 'type', 'messages_count', 'unread_messages_count',
                  'subject', 'icon', 'admins', 'users', 'last_message', 'about', 'messages_url', 'reply_url')

    def get_about(self, instance):
        # todo: map types
        if instance.type == CONVERSATION_TYPE_ABOUT_SHOUT:
            return ShoutSerializer(instance.attached_object, context=self.root.context).data
        return None

    def get_unread_messages_count(self, instance):
        return instance.unread_messages(self.context['request'].user).count()

    def get_messages_url(self, conversation):
        return reverse('conversation-messages', kwargs={'id': conversation.id}, request=self.context['request'])

    def get_reply_url(self, conversation):
        return reverse('conversation-reply', kwargs={'id': conversation.id}, request=self.context['request'])

    def to_internal_value(self, data):
        validated_data = super(ConversationSerializer, self).to_internal_value(data)
        return validated_data

    def validate_type(self, conversation_type):
        if conversation_type != 'public_chat':
            raise ValidationError({'type': "Only 'public_chat' conversations can be directly created"})
        return conversation_type

    def create(self, validated_data):
        user = self.context['request'].user
        conversation_type = ConversationType.texts[validated_data['get_type_display']]
        subject = validated_data['subject']
        icon = validated_data.get('icon', '')
        conversation = Conversation(creator=user, type=conversation_type, subject=subject, icon=icon, admins=[user.id])
        location_controller.update_object_location(conversation, user.location)
        conversation.save()
        conversation.users.add(user)
        return conversation


class PublicChatSerializer(serializers.Serializer):
    subject = serializers.CharField(max_length=25, allow_blank=True, default='')
    type = serializers.ChoiceField(choices=['public_chat'], help_text="Only 'public_chat' is allowed")


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
    type = serializers.CharField(source='get_type_display', help_text="Currently, either 'listen' or 'message'")
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
    type = serializers.CharField(source='get_type_display', help_text="Currently, either 'user' or 'shout'",
                                 read_only=True)
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

            if 'attached_user' in attached_object:
                validated_data['type'] = REPORT_TYPE_PROFILE

            if 'attached_shout' in attached_object:
                validated_data['type'] = REPORT_TYPE_SHOUT
        else:
            errors['attached_object'] = ["This field is required"]
        if errors:
            raise ValidationError(errors)

        return validated_data

    def create(self, validated_data):
        attached_object = None
        report_type = validated_data['type']

        if report_type == REPORT_TYPE_PROFILE:
            attached_object = User.objects.get(id=validated_data['attached_object']['attached_user']['id'])
        if report_type == REPORT_TYPE_SHOUT:
            attached_object = Shout.objects.get(id=validated_data['attached_object']['attached_shout']['id'])
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
        initial_user['ip'] = get_real_ip(self.context.get('request'))
        is_test = self.root.context.get('is_test')
        user = user_from_facebook_auth_response(facebook_access_token, initial_user, is_test)
        self.instance = user
        return ret


class GplusAuthSerializer(serializers.Serializer):
    gplus_code = serializers.CharField(max_length=500)
    user = UserDetailSerializer(required=False)

    def to_internal_value(self, data):
        ret = super(GplusAuthSerializer, self).to_internal_value(data)
        gplus_code = ret.get('gplus_code')
        initial_user = ret.get('user', {})
        initial_user['ip'] = get_real_ip(self.context.get('request'))
        is_test = self.root.context.get('is_test')
        user = user_from_gplus_code(gplus_code, initial_user, data.get('client_name'), is_test)
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
        name = data.get('name', 'user')
        names = name.split()
        if len(names) >= 2:
            data['first_name'] = " ".join(names[0:-1])
            data['last_name'] = names[-1]
        elif len(names) >= 1:
            data['first_name'] = names[0]
            data['last_name'] = random.randint(0, 999)
        else:
            data['first_name'] = 'user'
            data['last_name'] = random.randint(0, 999)

        ret = super(ShoutitSignupSerializer, self).to_internal_value(data)
        return ret

    def validate_email(self, email):
        email = email.lower()
        if User.exists(email=email):
            raise ValidationError(['Email is already used by another user.'])
        return email

    def create(self, validated_data):
        initial_user = validated_data.get('user', {})
        initial_user['ip'] = get_real_ip(self.context.get('request'))
        is_test = self.root.context.get('is_test')
        user = user_controller.user_from_shoutit_signup_data(validated_data, initial_user, is_test)
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
        location = initial_user.get('location') if initial_user else None
        try:
            user = User.objects.get(Q(email=email) | Q(username=email))
        except User.DoesNotExist:
            client_name = data.get('client_name')
            if client_name and client_name == 'shoutit-ios':
                # signup hack! act as signup if email is new and from ios only!
                request = self.root.context.get('request')
                username = generate_username()
                data.update({
                    'name': "user " + username
                })
                serializer = ShoutitSignupSerializer(data=data, context={'request': request})
                serializer.is_valid(raise_exception=True)
                serializer.validated_data['username'] = username
                self.instance = serializer.save()
                return serializer.validated_data
            else:
                raise ValidationError({'email': ['The email or username you entered do not belong to any account.']})

        if not user.check_password(password):
            raise ValidationError({'password': ['The password you entered is incorrect.']})
        self.instance = user
        if location:
            location_controller.update_profile_location(user.ap, location)
        return ret


class ShoutitVerifyEmailSerializer(serializers.Serializer):
    email = serializers.EmailField(required=False)

    def validate_email(self, email):
        user = self.context.get('request').user
        email = email.lower()
        if User.objects.filter(email=email).exclude(id=user.id).exists():
            raise ValidationError(['Email is already used by another user.'])
        return email

    def to_internal_value(self, data):
        ret = super(ShoutitVerifyEmailSerializer, self).to_internal_value(data)
        user = self.context.get('request').user
        email = ret.get('email')
        # if the email changed the model will take care of sending the verification emal
        if email:
            user.email = email.lower()
            user.save(update_fields=['email', 'is_activated'])
        else:
            user.send_verification_email()
        return ret


class ShoutitResetPasswordSerializer(serializers.Serializer):
    email = serializers.CharField()

    def to_internal_value(self, data):
        ret = super(ShoutitResetPasswordSerializer, self).to_internal_value(data)
        email = ret.get('email').lower()
        try:
            user = User.objects.get(Q(email=email) | Q(username=email))
            if not user.is_active:
                raise AuthenticationFailed('User inactive or deleted.')
        except User.DoesNotExist:
            raise ValidationError({'email': ['The email or username you entered do not belong to any account.']})
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
            user = ConfirmToken.objects.get(type=TOKEN_TYPE_RESET_PASSWORD, token=value, is_disabled=False).user
            if not user.is_active:
                raise AuthenticationFailed('User inactive or deleted.')
            self.instance = user
        except ConfirmToken.DoesNotExist:
            raise ValidationError(['Reset token is invalid.'])


class UserDeactivationSerializer(serializers.Serializer):
    password = serializers.CharField()

    def to_internal_value(self, data):
        ret = super(UserDeactivationSerializer, self).to_internal_value(data)
        password = ret.get('password')
        user = self.context.get('user')
        if not user.check_password(password):
            raise ValidationError({'password': ['The password you entered is incorrect.']})
        user.update(is_active=False)
        return ret


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
        fields = ('id', 'user', 'message', 'old_message', 'title', 'mobile', 'status', 'country', 'created_at')

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


# Backward compatibility with v3
ProfileDetailSerializer = UserDetailSerializer
ProfileSerializer = UserSerializer
