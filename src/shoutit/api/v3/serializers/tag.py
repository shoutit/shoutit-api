"""

"""
from __future__ import unicode_literals

from rest_framework import serializers
from rest_framework.reverse import reverse

from shoutit.models import Tag, FeaturedTag, Category
from shoutit.utils import url_with_querystring, blank_to_none


class TagSerializer(serializers.ModelSerializer):
    name = serializers.CharField(max_length=30)
    api_url = serializers.HyperlinkedIdentityField(view_name='tag-detail', lookup_field='name')

    class Meta:
        model = Tag
        fields = ('id', 'name', 'api_url', 'image')

    def to_internal_value(self, data):
        if isinstance(data, basestring):
            data = {'name': data}
        ret = super(TagSerializer, self).to_internal_value(data)
        return ret

    def to_representation(self, instance):
        ret = super(TagSerializer, self).to_representation(instance)
        blank_to_none(ret, ['image'])
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
        shouts_url = reverse('shout-list', request=self.context['request'])
        return url_with_querystring(shouts_url, tags=tag.name)


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
    name = serializers.CharField(read_only=True)
    slug = serializers.CharField()

    class Meta:
        model = Category
        fields = ('name', 'slug', 'icon', 'image')

    def to_internal_value(self, data):
        if isinstance(data, basestring):
            data = {'slug': data}
        super(CategorySerializer, self).to_internal_value(data)
        return self.instance

    def validate_slug(self, value):
        try:
            self.instance = Category.objects.get(slug=value)
        except (Category.DoesNotExist, AttributeError):
            raise serializers.ValidationError("Category with slug '%s' does not exist" % value)

    def to_representation(self, instance):
        ret = super(CategorySerializer, self).to_representation(instance)
        blank_to_none(ret, ['image', 'icon'])
        return ret


class CategoryDetailSerializer(CategorySerializer):
    filters = serializers.ListField(source='filter_objects')

    class Meta(CategorySerializer.Meta):
        parent_fields = CategorySerializer.Meta.fields
        fields = parent_fields + ('filters',)
