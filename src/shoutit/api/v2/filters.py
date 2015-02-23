# -*- coding: utf-8 -*-
"""

"""
from __future__ import unicode_literals
import django_filters
from rest_framework.exceptions import ValidationError
from rest_framework.filters import BaseFilterBackend
from shoutit.controllers import stream_controller
from shoutit.models import Trade


class ShoutFilter(django_filters.FilterSet):
    type = django_filters.MethodFilter(action='filter_type')
    min_price = django_filters.NumberFilter(name="item__Price", lookup_type='gte')
    max_price = django_filters.NumberFilter(name="item__Price", lookup_type='lte')
    tags = django_filters.MethodFilter(action='filter_tags')
    down_left_lat = django_filters.NumberFilter(name='latitude', lookup_type='gte')
    down_left_lng = django_filters.NumberFilter(name='longitude', lookup_type='gte')
    up_right_lat = django_filters.NumberFilter(name='latitude', lookup_type='lte')
    up_right_lng = django_filters.NumberFilter(name='longitude', lookup_type='lte')

    class Meta:
        model = Trade
        fields = ['id', 'country', 'city', 'type', 'min_price', 'max_price', 'tags',
                  'down_left_lat', 'down_left_lng', 'up_right_lat', 'up_right_lng']
        order_by = ['-date_published']

    def filter_type(self, queryset, value):
        if value not in ['all', 'offers', 'requests']:
            raise ValidationError({'type': "should be `all`, `requests` or `offers`."})
        return stream_controller.filter_posts_qs(queryset, value)

    def filter_tags(self, queryset, value):
        tags = value.replace(',', ' ').split()
        return stream_controller.filter_shouts_qs(queryset, tags)

