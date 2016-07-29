"""

"""
from __future__ import unicode_literals

from django.utils.translation import ugettext_lazy as _
from hvad.contrib.restframework import TranslatableModelSerializer
from rest_framework import serializers
from rest_framework.reverse import reverse

from shoutit.models import Tag, FeaturedTag, Category, TagKey
from shoutit.utils import url_with_querystring, blank_to_none


class MiniTagSerializer(TranslatableModelSerializer):
    name = serializers.CharField(read_only=True, source='_local_name')
    slug = serializers.CharField(read_only=True)

    class Meta:
        model = Tag
        fields = ('id', 'name', 'slug')
        extra_kwargs = {'id': {'required': False, 'read_only': False}}

    def compat_name(self, ret):
        request = self.context['request']
        from_web = hasattr(request.auth, 'client') and request.auth.client.name == 'shoutit-web'
        ios_condition = request.agent == 'ios' and request.build_no >= 22312
        android_condition = request.agent == 'android' and request.build_no >= 1450
        if not any([from_web, ios_condition, android_condition]):
            ret['name'] = ret['slug']
        return ret

    def to_representation(self, instance):
        ret = super(MiniTagSerializer, self).to_representation(instance)
        blank_to_none(ret, ['image'])
        # Compatibility for older clients expecting `name` to be the unique identifier of Tag object
        self.compat_name(ret)
        return ret


class TagSerializer(MiniTagSerializer):
    api_url = serializers.HyperlinkedIdentityField(view_name='tag-detail', lookup_field='slug')

    class Meta(MiniTagSerializer.Meta):
        parent_fields = MiniTagSerializer.Meta.fields
        fields = parent_fields + ('api_url', 'image')

    def to_internal_value(self, data):
        if isinstance(data, basestring):
            data = {'slug': data}
        ret = super(TagSerializer, self).to_internal_value(data)
        return ret


class TagDetailSerializer(TagSerializer):
    is_listening = serializers.SerializerMethodField(help_text="Whether logged in user is listening to this tag")
    listeners_url = serializers.HyperlinkedIdentityField(view_name='tag-listeners', lookup_field='slug',
                                                         help_text="URL to show listeners of this tag")
    shouts_url = serializers.SerializerMethodField(help_text="URL to show shouts with this tag")

    class Meta(TagSerializer.Meta):
        parent_fields = TagSerializer.Meta.fields
        fields = parent_fields + ('web_url', 'listeners_count', 'listeners_url', 'is_listening', 'shouts_url')

    def get_is_listening(self, tag):
        request = self.root.context.get('request')
        user = request and request.user
        return user and user.is_authenticated() and user.is_listening(tag)

    def get_shouts_url(self, tag):
        shouts_url = reverse('shout-list', request=self.context['request'])
        return url_with_querystring(shouts_url, tags=tag.slug)


class FeaturedTagSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source='tag.name')
    api_url = serializers.SerializerMethodField()
    image = serializers.URLField(source='tag.image')

    class Meta:
        model = FeaturedTag
        fields = ('id', 'title', 'name', 'api_url', 'image', 'rank')

    def get_api_url(self, f_tag):
        return reverse('tag-detail', kwargs={'name': f_tag.tag.name}, request=self.context['request'])


class TagKeySerializer(TranslatableModelSerializer):
    name = serializers.CharField(read_only=True, source='_local_name')
    slug = serializers.CharField(read_only=True)
    values = MiniTagSerializer(source='tags', many=True)

    class Meta:
        model = TagKey
        fields = ('name', 'slug', 'values')

    def to_representation(self, instance):
        ret = super(TagKeySerializer, self).to_representation(instance)
        if 'values' in ret:
            ret['values'].sort(key=lambda c: c['name'])
        return ret


class SingleValueTagKeySerializer(TagKeySerializer):
    value = MiniTagSerializer()

    class Meta(TagKeySerializer.Meta):
        fields = ('name', 'slug', 'value')


class CategorySerializer(TranslatableModelSerializer):
    name = serializers.CharField(read_only=True, source='_local_name')
    slug = serializers.CharField()

    class Meta:
        model = Category
        fields = ('name', 'slug', 'icon', 'image')

    def to_internal_value(self, data):
        if isinstance(data, basestring):
            data = {'slug': data}
        super(CategorySerializer, self).to_internal_value(data)
        return self.instance

    def validate_slug(self, slug):
        try:
            self.instance = Category.objects.get(slug=slug)
        except (Category.DoesNotExist, AttributeError):
            raise serializers.ValidationError(_("Category with slug '%(slug)s' does not exist") % {'value': slug})

    def to_representation(self, instance):
        ret = super(CategorySerializer, self).to_representation(instance)
        blank_to_none(ret, ['image', 'icon'])
        return ret


class CategoryDetailSerializer(CategorySerializer):
    filters = TagKeySerializer(many=True)

    class Meta(CategorySerializer.Meta):
        parent_fields = CategorySerializer.Meta.fields
        fields = parent_fields + ('filters',)

    def to_representation(self, instance):
        ret = super(CategoryDetailSerializer, self).to_representation(instance)
        if 'filters' in ret:
            ret['filters'].sort(key=lambda c: c['name'])
        return ret
