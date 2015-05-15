# -*- coding: utf-8 -*-
"""

"""
from __future__ import unicode_literals
from django.conf import settings
from django.db.models import Count
import django_filters
from rest_framework import filters
from rest_framework.exceptions import ValidationError
from common.utils import process_tags
from shoutit.controllers import stream_controller
from shoutit.models import Shout, Category, Tag, PredefinedCity
from elasticsearch_dsl import F
import logging
logger = logging.getLogger('shoutit.debug')


class ShoutFilter(django_filters.FilterSet):
    shout_type = django_filters.MethodFilter(action='filter_shout_type')
    min_price = django_filters.NumberFilter(name="item__price", lookup_type='gte')
    max_price = django_filters.NumberFilter(name="item__price", lookup_type='lte')
    tags = django_filters.MethodFilter(action='filter_tags')
    category = django_filters.MethodFilter(action='filter_category')
    down_left_lat = django_filters.NumberFilter(name='latitude', lookup_type='gte')
    down_left_lng = django_filters.NumberFilter(name='longitude', lookup_type='gte')
    up_right_lat = django_filters.NumberFilter(name='latitude', lookup_type='lte')
    up_right_lng = django_filters.NumberFilter(name='longitude', lookup_type='lte')
    user = django_filters.CharFilter(name='user__username')

    class Meta:
        model = Shout
        fields = ['id', 'country', 'city', 'shout_type', 'min_price', 'max_price', 'tags', 'category',
                  'down_left_lat', 'down_left_lng', 'up_right_lat', 'up_right_lng', 'user']
        order_by = ['-date_published']

    def filter_shout_type(self, queryset, value):
        if value not in ['all', 'offer', 'request']:
            raise ValidationError({'shout_type': "should be `all`, `request` or `offer`."})
        return stream_controller.filter_posts_qs(queryset, value)

    def filter_tags(self, queryset, value):
        tags = value.replace(',', ' ').split()
        return stream_controller.filter_shouts_qs_by_tags(queryset, tags)

    def filter_category(self, queryset, value):
        try:
            category = Category.objects.get(name=value)
            tags = category.tags.all()
            if not tags:
                return queryset
            return queryset.filter(tags__in=tags)
        except Category.DoesNotExist:
            raise ValidationError({'category': "Category '%s' does not exist" % value})


class ShoutIndexFilterBackend(filters.BaseFilterBackend):

    def filter_queryset(self, request, index_queryset, view):
        if view.action != 'list':
            return index_queryset

        data = request.query_params

        search = data.get('search')
        if search:
            index_queryset = index_queryset.query(
                'fuzzy_like_this', like_text=search, fields=['title', 'text', 'tags'], fuzziness=1)

        tags = data.get('tags')
        if tags:
            tags = tags.replace(',', ' ').split()
            tag_names = process_tags(tags)
            for tag_name in tag_names:
                index_queryset = index_queryset.filter('term', tags=tag_name)

        country = data.get('country')
        if country and country != 'all':
            index_queryset = index_queryset.filter('term', country=country)

        city = data.get('city')
        if city and city != 'all':
            f = [F('term', city=city)]
            try:
                pd_city = PredefinedCity.objects.get(city=city)
            except PredefinedCity.DoesNotExist:
                pass
            else:
                cities = pd_city.get_cities_within(settings.NEARBY_CITIES_RADIUS_KM)
                for nearby_city in cities:
                    f.append(F('term', city=nearby_city.city))
                city_f = F('bool', should=f)
                index_queryset = index_queryset.filter(city_f)

        category = data.get('category')
        if category:
            exists = Category.objects.filter(name=category).exists()
            if not exists:
                raise ValidationError({'category': "Category '%s' does not exist" % category})
            if category != 'all':
                index_queryset = index_queryset.filter('term', category=category)

        shout_type = data.get('shout_type')
        if shout_type:
            if shout_type not in ['all', 'offer', 'request']:
                raise ValidationError({'shout_type': "should be `all`, `request` or `offer`."})
            if shout_type != 'all':
                index_queryset = index_queryset.filter('term', type=shout_type)

        min_price = data.get('min_price')
        if min_price:
            index_queryset = index_queryset.filter('range', **{'price': {'gte': min_price}})

        max_price = data.get('max_price')
        if max_price:
            index_queryset = index_queryset.filter('range', **{'price': {'lte': max_price}})

        down_left_lat = data.get('down_left_lat')
        if down_left_lat:
            index_queryset = index_queryset.filter('range', **{'latitude': {'gte': down_left_lat}})

        down_left_lng = data.get('down_left_lng')
        if down_left_lng:
            index_queryset = index_queryset.filter('range', **{'longitude': {'gte': down_left_lng}})

        up_right_lat = data.get('up_right_lat')
        if up_right_lat:
            index_queryset = index_queryset.filter('range', **{'latitude': {'lte': up_right_lat}})

        up_right_lng = data.get('up_right_lng')
        if up_right_lng:
            index_queryset = index_queryset.filter('range', **{'longitude': {'lte': up_right_lng}})

        # sort
        sort = data.get('sort')
        sort_types = {
            None: ('-date_published',),
            'time': ('-date_published',),
            'price_asc': ('price',),
            'price_desc': ('-price',),
        }
        if sort and sort not in sort_types:
                raise ValidationError({'sort': "Invalid sort."})
        # selected_sort = ('-priority',) + sort_types[sort]
        selected_sort = sort_types[sort]
        if search:
            selected_sort = ('_score',) + selected_sort
        index_queryset = index_queryset.sort(*selected_sort)

        logger.debug(index_queryset.to_dict())
        return index_queryset


class TagFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(lookup_type='icontains')
    type = django_filters.MethodFilter(action='filter_type')
    country = django_filters.MethodFilter(action='filter_country')
    city = django_filters.MethodFilter(action='filter_city')
    category = django_filters.MethodFilter(action='filter_category')

    class Meta:
        model = Tag
        fields = ('name', 'type', 'country', 'city')

    def filter_type(self, queryset, value):
        if value not in ['all', 'top', 'featured']:
            raise ValidationError({'type': "should be `all`, `top` or `featured`."})

        if value == 'featured':
            queryset = queryset.annotate(c=Count('featured_in')).filter(c__gte=1)
        return queryset

    def filter_country(self, queryset, value):
        tag_type = 'type' in self.data and self.data['type']
        if tag_type not in ['top', 'featured']:
            raise ValidationError({'country': "only works when type equals `top` or `featured`."})

        if tag_type == 'featured':
            queryset = queryset.filter(featured_in__country=value)
        return queryset

    def filter_city(self, queryset, value):
        tag_type = 'type' in self.data and self.data['type']
        if tag_type not in ['top', 'featured']:
            raise ValidationError({'city': "only works when type equals `top` or `featured`."})

        if tag_type == 'featured':
            queryset = queryset.filter(featured_in__city=value)
        return queryset

    def filter_category(self, queryset, value):
        try:
            category = Category.objects.get(name=value)
            # return all tags that belong to the category except the main tag
            # todo: check if we really need to exclude the main tag or not
            # return queryset.filter(category=category).filter(~Q(id=category.main_tag_id))
            return queryset.filter(category=category)
        except Category.DoesNotExist:
            raise ValidationError({'category': "Category '%s' does not exist" % value})
