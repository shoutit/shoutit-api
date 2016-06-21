"""

"""
from __future__ import unicode_literals

from rest_framework import serializers

from shoutit.models import PageCategory
from shoutit.utils import blank_to_none
from .base import RecursiveSerializer


class PageCategorySerializer(serializers.ModelSerializer):
    children = RecursiveSerializer(many=True)

    class Meta:
        model = PageCategory
        fields = ['id', 'name', 'slug', 'children']

    def to_representation(self, instance):
        ret = super(PageCategorySerializer, self).to_representation(instance)
        blank_to_none(ret, ['image', 'cover', 'icon'])
        return ret
