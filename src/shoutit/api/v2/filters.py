# -*- coding: utf-8 -*-
"""

"""
from __future__ import unicode_literals

from django.conf import settings
from django.db.models import Q
import django_filters
from rest_framework import filters
from rest_framework.exceptions import ValidationError
from elasticsearch_dsl import F
from common.constants import COUNTRIES

from common.utils import process_tags
from shoutit.models import Category, Tag, PredefinedCity, FeaturedTag
from shoutit.utils import debug_logger, error_logger


class ShoutIndexFilterBackend(filters.BaseFilterBackend):
    def filter_queryset(self, request, index_queryset, view, extra_query_params=None):
        data = request.query_params.copy()
        if isinstance(extra_query_params, dict):
            data.update(extra_query_params)

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

            # todo: add state
            city = data.get('city')
            if city and city != 'all':
                f = [F('term', city=city)]
                # todo: use other means of finding the surrounding cities like state.
                try:
                    pd_city = PredefinedCity.objects.filter(city=city, country=country)[0]
                except IndexError:
                    pass
                else:
                    cities = pd_city.get_cities_within(settings.NEARBY_CITIES_RADIUS_KM)
                    for nearby_city in cities:
                        f.append(F('term', city=nearby_city.city))
                    city_f = F('bool', should=f)
                    index_queryset = index_queryset.filter(city_f)

        category = data.get('category')
        if category and category != 'all':
            try:
                category = Category.objects.get(Q(name=category) | Q(slug=category))
            except Category.DoesNotExist:
                raise ValidationError({'category': ["Category with name or slug '%s' does not exist" % category]})
            else:
                index_queryset = index_queryset.filter('term', category=category.name)

        shout_type = data.get('shout_type')
        if shout_type:
            if shout_type not in ['all', 'offer', 'request']:
                raise ValidationError({'shout_type': ["should be `all`, `request` or `offer`."]})
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
            raise ValidationError({'sort': ["Invalid sort."]})
        # selected_sort = ('-priority',) + sort_types[sort]
        selected_sort = sort_types[sort]
        if search:
            selected_sort = ('_score',) + selected_sort
        index_queryset = index_queryset.sort(*selected_sort)

        debug_logger.debug(index_queryset.to_dict())
        return index_queryset


class HomeFilterBackend(filters.BaseFilterBackend):
    def filter_queryset(self, request, index_queryset, view):
        user = view.get_object()
        country = user.location.get('country')
        data = request.query_params
        listening = []
        if country:
            index_queryset = index_queryset.filter('term', country=country)

        # Listened Tags
        tags = user.listening2_tags_names
        if tags:
            for t in tags:
                listening.append(F('term', tags=t))

        # Listened Users + user himself
        users = [user.pk] + user.listening2_pages_ids + user.listening2_users_ids
        if users:
            for u in users:
                listening.append(F('term', uid=u))

        listening_filter = F('bool', should=listening)
        index_queryset = index_queryset.filter(listening_filter)

        # sort
        sort = data.get('sort')
        sort_types = {
            None: ('-date_published',),
            'time': ('-date_published',),
            'price_asc': ('price',),
            'price_desc': ('-price',),
        }
        if sort and sort not in sort_types:
            raise ValidationError({'sort': ["Invalid sort."]})
        # selected_sort = ('-priority',) + sort_types[sort]
        selected_sort = sort_types[sort]
        index_queryset = index_queryset.sort(*selected_sort)

        debug_logger.debug(index_queryset.to_dict())
        return index_queryset


class DiscoverItemFilter(filters.BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        if view.action != 'list':
            return queryset

        data = request.query_params
        country = data.get('country', '')
        if country not in COUNTRIES:
            raise ValidationError({'country': ["Invalid country code"]})

        country_queryset = queryset.filter(countries__contains=[country])
        no_country_queryset = queryset.filter(countries__contained_by=[''])
        if country != '' and country_queryset.count() != 0:
            queryset = country_queryset
        else:
            queryset = no_country_queryset
        return queryset


class TagFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(lookup_type='icontains')
    type = django_filters.MethodFilter(action='filter_type')
    category = django_filters.MethodFilter(action='filter_category')
    country = django_filters.MethodFilter(action='filter_country')
    state = django_filters.MethodFilter(action='filter_state')
    city = django_filters.MethodFilter(action='filter_city')

    class Meta:
        model = Tag
        fields = ('name', 'type', 'category', 'country', 'state', 'city')

    def filter_type(self, queryset, value):
        if value not in ['all', 'top', 'featured']:
            raise ValidationError({'type': ["should be `all`, `top` or `featured`."]})

        if value == 'featured':
            queryset = FeaturedTag.objects.all().order_by('rank')
            queryset = self.filter_location(queryset)
        return queryset

    def filter_category(self, queryset, value):
        tag_type = self.data.get('type')
        if tag_type == 'featured':
            raise ValidationError({'category': ["does not work when type is `featured`."]})
        try:
            category = Category.objects.get(name=value)
            # return all tags that belong to the category except the main tag
            # todo: check if we really need to exclude the main tag or not
            # return queryset.filter(category=category).filter(~Q(id=category.main_tag_id))
            return queryset.filter(category=category)
        except Category.DoesNotExist:
            raise ValidationError({'category': ["Category '%s' does not exist" % value]})

    def filter_country(self, queryset, value):
        tag_type = self.data.get('type')
        if tag_type not in ['top', 'featured']:
            raise ValidationError({'country': ["only works when type equals `top` or `featured`."]})
        return queryset

    def filter_state(self, queryset, value):
        tag_type = self.data.get('type')
        if tag_type not in ['top', 'featured']:
            raise ValidationError({'state': ["only works when type equals `top` or `featured`."]})
        return queryset

    def filter_city(self, queryset, value):
        tag_type = self.data.get('type')
        if tag_type not in ['top', 'featured']:
            raise ValidationError({'city': ["only works when type equals `top` or `featured`."]})
        return queryset

    def filter_location(self, queryset):
        country = self.data.get('country', '')
        state = self.data.get('state', '')
        city = self.data.get('city', '')

        # country
        if country:
            country_qs = queryset.filter(country=country)
            if not country_qs:
                country = ''
                country_qs = queryset.filter(country=country)
            queryset = country_qs

            # state
            if country:
                if state:
                    state_qs = queryset.filter(state=state)
                    if not state_qs:
                        state = ''
                        state_qs = queryset.filter(state=state)
                    queryset = state_qs

                    # city
                    if state:
                        if city:
                            city_qs = queryset.filter(city=city)
                            if not city_qs:
                                city = ''
                                city_qs = queryset.filter(city=city)
                            queryset = city_qs
                        else:
                            queryset = queryset.filter(city=city)
                else:
                    queryset = queryset.filter(state=state)
        else:
            queryset = queryset.filter(country=country)

        if not queryset:
            queryset = queryset.filter(country='')
            error_logger.warn("Discover returned 0 Featured Tags.", extra={
                'country': country, 'state': state, 'city': city,
            })
        return queryset
