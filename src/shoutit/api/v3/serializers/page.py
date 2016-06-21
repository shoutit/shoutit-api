"""

"""
from __future__ import unicode_literals

from rest_framework import serializers

from shoutit.models import PageCategory
from shoutit.utils import blank_to_none
from .base import RecursiveSerializer
from .profile import ObjectProfileActionSerializer


class PageCategorySerializer(serializers.ModelSerializer):
    slug = serializers.CharField()
    children = RecursiveSerializer(many=True, read_only=True)

    class Meta:
        model = PageCategory
        fields = ['id', 'name', 'slug', 'children']
        extra_kwargs = {'name': {'read_only': True}}

    def to_representation(self, instance):
        ret = super(PageCategorySerializer, self).to_representation(instance)
        blank_to_none(ret, ['image', 'cover', 'icon'])
        return ret

    def to_internal_value(self, data):
        if isinstance(data, basestring):
            data = {'slug': data}
        super(PageCategorySerializer, self).to_internal_value(data)
        return self.instance

    def validate_slug(self, value):
        try:
            self.instance = PageCategory.objects.get(slug=value)
        except (PageCategory.DoesNotExist, AttributeError):
            raise serializers.ValidationError("PageCategory with slug '%s' does not exist" % value)


class AddAdminSerializer(ObjectProfileActionSerializer):
    success_message = "Added %s to the admins of this page"

    def condition(self, instance, actor, profile):
        return True

    def update(self, instance, validated_data):
        profile = self.fields['profile'].instance
        if not instance.is_admin(profile):
            instance.add_admin(profile)
        else:
            self.success_message = "%s is already admin in this page"
        return instance


class RemoveAdminSerializer(ObjectProfileActionSerializer):
    error_message = "%s is not admin in this page"
    success_message = "Removed %s from the admins of this page"

    def condition(self, instance, actor, profile):
        return instance.is_admin(profile)

    def update(self, instance, validated_data):
        profile = self.fields['profile'].instance
        instance.remove_admin(profile)
        return instance
