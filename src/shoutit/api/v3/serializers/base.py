"""

"""
from __future__ import unicode_literals

from ipware.ip import get_real_ip
from rest_framework import serializers

from shoutit.controllers import location_controller
from shoutit.models import Video, PredefinedCity

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
