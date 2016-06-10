"""

"""
from __future__ import unicode_literals

import uuid

from ipware.ip import get_real_ip
from push_notifications.apns import apns_send_bulk_message
from push_notifications.gcm import gcm_send_bulk_message
from rest_framework import serializers

from shoutit.controllers import location_controller
from shoutit.models import Video, PredefinedCity
from ..exceptions import ERROR_REASON

empty_char_input = {'allow_blank': True, 'allow_null': True, 'required': False}


class LocationSerializer(serializers.Serializer):
    latitude = serializers.FloatField(min_value=-90, max_value=90, required=False)
    longitude = serializers.FloatField(min_value=-180, max_value=180, required=False)
    country = serializers.CharField(min_length=2, max_length=2, required=False, allow_blank=True)
    postal_code = serializers.CharField(max_length=10, required=False, allow_blank=True)
    state = serializers.CharField(max_length=50, required=False, allow_blank=True)
    city = serializers.CharField(max_length=100, required=False, allow_blank=True)
    address = serializers.CharField(max_length=200, required=False, allow_blank=True)

    def to_internal_value(self, data):
        validated_data = super(LocationSerializer, self).to_internal_value(data)
        lat = 'latitude' in validated_data
        lng = 'longitude' in validated_data
        country = 'country' in validated_data
        city = 'city' in validated_data
        address = validated_data.pop('address', None)
        request = self.root.context.get('request')
        ip = get_real_ip(request) if request else None

        if lat and lng and country and city:
            location = validated_data
        elif lat and lng:
            # Get location attributes using latitude, longitude or IP
            location = location_controller.from_location_index(validated_data.get('latitude'),
                                                               validated_data.get('longitude'), ip)
        elif request and request.user.is_authenticated():
            # Update the logged in user address
            location = request.user.location
        elif ip:
            # Get location attributes using IP
            location = location_controller.from_ip(ip, use_location_index=True)
        else:
            raise serializers.ValidationError("Could not find (`latitude` and `longitude`) or figure the IP Address")

        if address:
            location.update({'address': address})
        validated_data.update(location)
        return validated_data


class PushTokensSerializer(serializers.Serializer):
    apns = serializers.CharField(max_length=64, allow_null=True, required=False)
    gcm = serializers.CharField(allow_null=True, required=False)

    def to_internal_value(self, data):
        ret = super(PushTokensSerializer, self).to_internal_value(data)
        apns = ret.get('apns')
        gcm = ret.get('gcm')
        if apns and gcm:
            raise serializers.ValidationError("Only one of `apns` or `gcm` is required not both")
        return ret


class VideoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Video
        fields = ('url', 'thumbnail_url', 'provider', 'id_on_provider', 'duration')


class PredefinedCitySerializer(serializers.ModelSerializer):
    class Meta:
        model = PredefinedCity
        fields = ('id', 'country', 'postal_code', 'state', 'city', 'latitude', 'longitude')


class AttachedUUIDObjectMixin(object):
    def to_internal_attached_value(self, data, force_validation=False):
        from .message import MessageAttachmentSerializer
        from .conversation import ConversationProfileActionSerializer
        from .notification import AttachedObjectSerializer
        model = self.Meta.model
        # Make sure no empty JSON body was posted
        if not data:
            data = {}
        # Validate the id only
        if force_validation or isinstance(self.parent, (MessageAttachmentSerializer, AttachedObjectSerializer, ConversationProfileActionSerializer)):
            if not isinstance(data, dict):
                raise serializers.ValidationError('Invalid data. Expected a dictionary, but got %s' % type(data).__name__)
            object_id = data.get('id')
            if object_id == '':
                raise serializers.ValidationError({'id': 'This field can not be empty'})
            if object_id:
                try:
                    uuid.UUID(object_id)
                    instance = model.objects.filter(id=object_id).first()
                except (ValueError, TypeError, AttributeError):
                    raise serializers.ValidationError({'id': "'%s' is not a valid id" % object_id})
                else:
                    if not instance:
                        raise serializers.ValidationError({'id': "%s with id '%s' does not exist" % (model.__name__, object_id)})
                    # Todo: utilize the fetched instance
                    self.instance = instance
                    return {'id': object_id}
            else:
                raise serializers.ValidationError({'id': ("This field is required", ERROR_REASON.REQUIRED)})


class PushTestSerializer(serializers.Serializer):
    apns = serializers.CharField(required=False)
    gcm = serializers.CharField(required=False)
    payload = serializers.DictField()

    def validate_payload(self, value):
        aps = value.get('aps')
        if aps is not None:
            if not isinstance(aps, dict) or aps.keys() == []:
                raise serializers.ValidationError({'aps': "Must be a non-empty dictionary"})
            valid_keys = ['alert', 'badge', 'sound', 'category', 'expiration', 'priority']
            if not all([k in valid_keys for k in aps.keys()]):
                raise serializers.ValidationError({'aps': "can only contain %s" % ", ".join(valid_keys)})
        return value

    def create(self, validated_data):
        apns = validated_data.get('apns')
        gcm = validated_data.get('gcm')
        payload = validated_data.get('payload', {})
        aps = payload.pop('aps', {})
        alert = aps.pop('alert', {})

        if apns:
            apns_send_bulk_message(registration_ids=[apns], alert=alert, extra=payload, **aps)
        if gcm:
            gcm_send_bulk_message(registration_ids=[gcm], data=payload)

        return True
