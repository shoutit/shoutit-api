"""

"""
from __future__ import unicode_literals

import uuid

from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from rest_framework import serializers
from rest_framework.reverse import reverse

from common.constants import POST_TYPE_REQUEST, POST_TYPE_OFFER
from shoutit.controllers import shout_controller
from shoutit.models import Shout, Currency, InactiveShout
from shoutit.utils import upload_image_to_s3, debug_logger, blank_to_none
from .base import LocationSerializer, VideoSerializer, empty_char_input
from .profile import ProfileSerializer
from .tag import CategorySerializer
from ..exceptions import ERROR_REASON


class ShoutSerializer(serializers.ModelSerializer):
    type = serializers.ChoiceField(source='get_type_display', choices=['offer', 'request'], help_text="*")
    location = LocationSerializer(
        help_text="Defaults to user's saved location, Passing the `latitude` and `longitude` is enough to calculate new location properties")
    title = serializers.CharField(source='item.name', min_length=4, max_length=50, help_text="Max 50 characters", **empty_char_input)
    text = serializers.CharField(min_length=10, max_length=1000, help_text="Max 1000 characters", **empty_char_input)
    price = serializers.IntegerField(source='item.price', allow_null=True, required=False, help_text="Value in cents")
    available_count = serializers.IntegerField(default=1, help_text="Only used for Offers")
    is_sold = serializers.BooleanField(default=False, help_text="Only used for Offers")

    currency = serializers.CharField(source='item.currency_code', allow_null=True, required=False,
                                     help_text="3 characters currency code taken from the list of available currencies")
    date_published = serializers.IntegerField(source='date_published_unix', read_only=True)
    profile = ProfileSerializer(source='user', read_only=True)
    category = CategorySerializer(help_text="Either Category object or simply the category `slug`")
    filters = serializers.ListField(default=list, )
    api_url = serializers.SerializerMethodField()

    class Meta:
        model = Shout
        fields = ('id', 'api_url', 'web_url', 'type', 'category', 'title', 'location', 'text', 'price', 'currency',
                  'available_count', 'is_sold', 'thumbnail', 'video_url', 'profile', 'date_published', 'filters')

    def get_api_url(self, shout):
        return reverse('shout-detail', kwargs={'id': shout.id}, request=self.context['request'])

    def validate_currency(self, value):
        if not value:
            return None
        try:
            if not isinstance(value, basestring):
                raise ValueError()
            return Currency.objects.get(code__iexact=value)
        except (Currency.DoesNotExist, ValueError):
            raise serializers.ValidationError('Invalid currency')

    def to_internal_value(self, data):
        from .message import MessageAttachmentSerializer
        from .notification import AttachedObjectSerializer
        # Make sure no empty JSON body was posted
        if not data:
            data = {}
        # validate the id only when sharing the shout as message attachment
        if isinstance(self.parent, (MessageAttachmentSerializer, AttachedObjectSerializer)):
            if not isinstance(data, dict):
                raise serializers.ValidationError('Invalid data. Expected a dictionary, but got %s' % type(data).__name__)
            shout_id = data.get('id')
            if shout_id == '':
                raise serializers.ValidationError({'id': 'This field can not be empty'})
            if shout_id:
                try:
                    uuid.UUID(shout_id)
                    if not Shout.objects.filter(id=shout_id).exists():
                        raise serializers.ValidationError({'id': "Shout with id '%s' does not exist" % shout_id})
                    return {'id': shout_id}
                except (ValueError, TypeError, AttributeError):
                    raise serializers.ValidationError({'id': "'%s' is not a valid id" % shout_id})
            else:
                raise serializers.ValidationError({'id': ("This field is required", ERROR_REASON.REQUIRED)})

        # Optional price and currency
        price = data.get('price')
        price_is_set = price is not None
        currency_is_none = data.get('currency') is None
        if price_is_set and price != 0 and currency_is_none:
            raise serializers.ValidationError({'currency': "The currency must be set when the price is set"})
        # Optional category defaults to "Other"
        if data.get('category') is None:
            data['category'] = 'other'
        # Optional location defaults to user's saved location
        if data.get('location') is None:
            data['location'] = {}
        ret = super(ShoutSerializer, self).to_internal_value(data)
        return ret

    def to_representation(self, instance):
        if instance.muted or instance.is_disabled:
            return InactiveShout().to_dict
        ret = super(ShoutSerializer, self).to_representation(instance)
        blank_to_none(ret, ['title', 'text'])
        return ret


class ShoutDetailSerializer(ShoutSerializer):
    images = serializers.ListField(source='item.images', child=serializers.URLField(), required=False)
    videos = VideoSerializer(source='item.videos.all', many=True, required=False)
    publish_to_facebook = serializers.BooleanField(write_only=True, required=False)
    reply_url = serializers.SerializerMethodField(
        help_text="URL to reply to this shout if possible, not set for shout owner")
    conversations = serializers.SerializerMethodField()
    mobile = serializers.CharField(min_length=4, max_length=20, write_only=True, **empty_char_input)
    mobile_hint = serializers.CharField(read_only=True)
    is_mobile_set = serializers.BooleanField(read_only=True)

    class Meta(ShoutSerializer.Meta):
        parent_fields = ShoutSerializer.Meta.fields
        fields = parent_fields + ('images', 'videos', 'published_on', 'publish_to_facebook', 'reply_url',
                                  'conversations', 'mobile', 'mobile_hint', 'is_mobile_set')

    def get_reply_url(self, shout):
        return reverse('shout-reply', kwargs={'id': shout.id}, request=self.context['request'])

    def get_conversations(self, shout):
        from .message import ConversationSerializer
        user = self.root.context['request'].user
        if isinstance(user, AnonymousUser):
            return []
        conversations = shout.conversations.filter(users=user)
        return ConversationSerializer(conversations, many=True, context=self.root.context).data

    def to_representation(self, instance):
        if instance.muted or instance.is_disabled:
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
                s3_image = upload_image_to_s3(bucket='shoutit-shout-image-original', url=image,
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
        price = item.get('price')
        currency = item.get('currency_code')
        available_count = validated_data.get('available_count')
        is_sold = validated_data.get('is_sold')

        category = validated_data.get('category')
        filters = validated_data.get('filters')

        location = validated_data.get('location')
        publish_to_facebook = validated_data.get('publish_to_facebook')
        mobile = validated_data.get('mobile')

        images = item.get('images', None)
        videos = item.get('videos', {'all': None})['all']

        request = self.root.context.get('request')
        profile = getattr(request, 'profile', None) or getattr(request, 'user', None)or self.root.context.get('user')
        page_admin_user = getattr(request, 'page_admin_user', None)

        if not shout:
            case_1 = shout_type is POST_TYPE_REQUEST and title
            case_2 = shout_type is POST_TYPE_OFFER and (title or images or videos)
            if not (case_1 or case_2):
                raise serializers.ValidationError("Not enough info to create a shout")
            shout = shout_controller.create_shout(
                user=profile, shout_type=shout_type, title=title, text=text, price=price, currency=currency,
                available_count=available_count, is_sold=is_sold, category=category, filters=filters, location=location,
                images=images, videos=videos, page_admin_user=page_admin_user, publish_to_facebook=publish_to_facebook,
                mobile=mobile
            )
        else:
            # Todo: Check when updating shouts not to break requirements [case_1, case_2] better have that done at class level
            shout = shout_controller.edit_shout(
                shout, title=title, text=text, price=price, currency=currency, available_count=available_count,
                is_sold=is_sold, category=category, filters=filters, location=location, images=images, videos=videos,
                page_admin_user=page_admin_user, mobile=mobile
            )
        return shout


class CurrencySerializer(serializers.ModelSerializer):
    class Meta:
        model = Currency
        fields = ('code', 'country', 'name')
