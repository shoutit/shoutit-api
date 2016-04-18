"""

"""
from __future__ import unicode_literals

from rest_framework import serializers
from rest_framework.reverse import reverse
from rest_framework.settings import api_settings

from shoutit.models import DiscoverItem
from shoutit.utils import url_with_querystring


class DiscoverItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = DiscoverItem
        fields = ('id', 'api_url', 'title', 'subtitle', 'position', 'image', 'icon')
        extra_kwargs = {api_settings.URL_FIELD_NAME: {'view_name': 'discover-detail'}}

    def to_representation(self, instance):
        ret = super(DiscoverItemSerializer, self).to_representation(instance)
        if not ret.get('image'):
            ret['image'] = None
        if not ret.get('cover'):
            ret['cover'] = None
        if not ret.get('icon'):
            ret['icon'] = None
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
            ret['image'] = None
        if not ret.get('cover'):
            ret['cover'] = None
        if not ret.get('icon'):
            ret['icon'] = None
        return ret

    def get_shouts_url(self, discover_item):
        shouts_url = reverse('shout-list', request=self.context['request'])
        return url_with_querystring(shouts_url, discover=discover_item.pk)
