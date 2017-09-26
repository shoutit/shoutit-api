"""

"""
from hvad.contrib.restframework import TranslatableModelSerializer
from rest_framework import serializers
from rest_framework.reverse import reverse
from rest_framework.settings import api_settings

from shoutit.models import DiscoverItem
from shoutit.utils import url_with_querystring, blank_to_none


class DiscoverItemSerializer(TranslatableModelSerializer):
    title = serializers.CharField(read_only=True, source='_local_title')
    subtitle = serializers.CharField(read_only=True, source='_local_subtitle')

    class Meta:
        model = DiscoverItem
        fields = ('id', 'api_url', 'web_url', 'app_url', 'title', 'subtitle', 'position', 'image', 'icon')
        extra_kwargs = {api_settings.URL_FIELD_NAME: {'view_name': 'discover-detail'}}

    def to_representation(self, instance):
        ret = super(DiscoverItemSerializer, self).to_representation(instance)
        blank_to_none(ret, ['image', 'cover', 'icon'])
        return ret


class DiscoverItemDetailSerializer(DiscoverItemSerializer):
    description = serializers.CharField(read_only=True, source='_local_description')
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
        blank_to_none(ret, ['image', 'cover', 'icon'])
        # Sort children
        ret['children'] = sorted(ret['children'], key=lambda x: x['position'])
        return ret

    def get_shouts_url(self, discover_item):
        shouts_url = reverse('shout-list', request=self.context['request'])
        return url_with_querystring(shouts_url, discover=discover_item.pk)
