# -*- coding: utf-8 -*-
"""

"""
from __future__ import unicode_literals

import django_filters
from django.conf import settings
from elasticsearch_dsl import Search, Q
from rest_framework import filters

from common.constants import TAG_TYPE_STR, TAG_TYPE_INT
from common.utils import process_tags
from shoutit.api.v3.exceptions import InvalidParameter
from shoutit.models import Category, Tag, PredefinedCity, FeaturedTag, TagKey, DiscoverItem, User
from shoutit.utils import debug_logger, error_logger


class ShoutIndexFilterBackend(filters.BaseFilterBackend):
    def filter_queryset(self, request, index_queryset, view, extra_query_params=None):
        if not isinstance(index_queryset, Search):
            return index_queryset

        # Copy the query dict to be able to modify it as it is immutable, then update it with extra params
        data = request.query_params.copy()
        if isinstance(extra_query_params, dict):
            data.update(extra_query_params)

        # Update data from discover item shouts query if discover is passed
        discover = data.get('discover')
        if discover:
            try:
                discover_item = DiscoverItem.objects.get(id=discover)
            except ValueError:
                raise InvalidParameter('discover', "Invalid discover id")
            except DiscoverItem.DoesNotExist:
                msg = "Discover Item with id '%s' does not exist" % discover
                raise InvalidParameter('discover', msg)
            else:
                data.update(discover_item.shouts_query)

        # Filter shouts by user id if user username or id are passed in `user` query param
        user = data.get('profile') or data.get('user')
        if user:
            if user == 'me' and request.user.is_authenticated():
                user = request.user.username
            try:
                user_id = User.objects.get(username=user).pk
            except User.DoesNotExist:
                msg = "Profile with username '%s' does not exist" % user
                raise InvalidParameter('profile', msg)
            else:
                index_queryset = index_queryset.filter('term', uid=user_id)

        # Exclude ids
        exclude_ids = data.get('exclude_ids')
        if isinstance(exclude_ids, basestring):
            exclude_ids = exclude_ids.split(',')
        if exclude_ids:
            index_queryset = index_queryset.filter(~Q('terms', _id=exclude_ids))

        # Shout type
        shout_type = data.get('shout_type')
        if shout_type:
            if shout_type not in ['all', 'offer', 'request']:
                msg = "should be `all`, `request` or `offer`"
                raise InvalidParameter('shout_type', msg)
            if shout_type != 'all':
                index_queryset = index_queryset.filter('term', type=shout_type)

        # Search query
        search = data.get('search')
        if search:
            index_queryset = index_queryset.query(
                'multi_match', query=search, fields=['title', 'text', 'tags'], fuzziness='AUTO')

        # Tags
        tags = data.get('tags')
        if tags:
            tags = tags.replace(',', ' ').split()
            tag_names = process_tags(tags)
            index_queryset = index_queryset.filter('terms', tags=tag_names)

        # Location: Country, State, City, Latitude, Longitude
        country = data.get('country')
        if country and country != 'all':
            index_queryset = index_queryset.filter('term', country=country)
            # todo: add state
            city = data.get('city')
            if city and city != 'all':
                cities = [city]
                # todo: use other means of finding the surrounding cities like state.
                try:
                    pd_city = PredefinedCity.objects.filter(city=city, country=country)[0]
                except IndexError:
                    pass
                else:
                    nearby_cities = pd_city.get_cities_within(settings.NEARBY_CITIES_RADIUS_KM)
                    for nearby_city in nearby_cities:
                        cities.append(nearby_city.city)
                    index_queryset = index_queryset.filter('terms', city=cities)

        down_left_lat = data.get('down_left_lat')
        down_left_lng = data.get('down_left_lng')
        up_right_lat = data.get('up_right_lat')
        up_right_lng = data.get('up_right_lng')
        latlng_key = ''
        try:
            if down_left_lat:
                latlng_key = 'down_left_lat'
                down_left_lat = float(down_left_lat)
                up_right_lat = up_right_lat or 90
                if down_left_lat > float(up_right_lat) or not (90 >= down_left_lat >= -90):
                    raise InvalidParameter('down_left_lat',
                                           "Should be between -90 and 90, also not greater than 'up_right_lat'")
                index_queryset = index_queryset.filter('range', **{'latitude': {'gte': down_left_lat}})
            if down_left_lng:
                latlng_key = 'down_left_lng'
                down_left_lng = float(down_left_lng)
                up_right_lng = up_right_lng or 180
                if down_left_lng > float(up_right_lng) or not (180 >= down_left_lng >= -180):
                    raise InvalidParameter('down_left_lng',
                                           "Should be between -180 and 180, also not greater than 'up_right_lng'")
                index_queryset = index_queryset.filter('range', **{'longitude': {'gte': down_left_lng}})
            if up_right_lat:
                latlng_key = 'up_right_lat'
                if not (90 >= float(up_right_lat) >= -90):
                    raise InvalidParameter('up_right_lat', "Should be between -90 and 90")
                index_queryset = index_queryset.filter('range', **{'latitude': {'lte': up_right_lat}})
            if up_right_lng:
                latlng_key = 'up_right_lng'
                if not (180 >= float(up_right_lng) >= -180):
                    raise InvalidParameter('up_right_lng', "Should be between -180 and 180")
                index_queryset = index_queryset.filter('range', **{'longitude': {'lte': up_right_lng}})
        except ValueError:
            raise InvalidParameter(latlng_key, "Invalid number")

        # Category and Tags2
        category = data.get('category')
        if category and category != 'all':
            try:
                category = Category.objects.get(slug=category)
            except Category.DoesNotExist:
                raise InvalidParameter('category', "Category with slug '%s' does not exist" % category)
            else:
                index_queryset = index_queryset.filter('terms', category=[category.name, category.slug])
                cat_filters = TagKey.objects.filter(key__in=category.filters).values_list('key', 'values_type')
                for cat_f_key, cat_f_type in cat_filters:
                    if cat_f_type == TAG_TYPE_STR:
                        cat_f_param = data.get(cat_f_key)
                        if cat_f_param:
                            index_queryset = index_queryset.filter('term', **{'tags2__%s' % cat_f_key: cat_f_param})
                    elif cat_f_type == TAG_TYPE_INT:
                        for m1, m2 in [('min', 'gte'), ('max', 'lte')]:
                            cat_f_param = data.get('%s_%s' % (m1, cat_f_key))
                            if cat_f_param:
                                index_queryset = index_queryset.filter('range',
                                                                       **{'tags2__%s' % cat_f_key: {m2: cat_f_param}})

        # Price
        min_price = data.get('min_price')
        if min_price:
            index_queryset = index_queryset.filter('range', **{'price': {'gte': min_price}})

        max_price = data.get('max_price')
        if max_price:
            index_queryset = index_queryset.filter('range', **{'price': {'lte': max_price}})

        # Sorting
        sort = data.get('sort')
        sort_types = {
            None: ('-date_published',),
            'time': ('-date_published',),
            'price_asc': ('price',),
            'price_desc': ('-price',),
        }
        if sort and sort not in sort_types:
            raise InvalidParameter('sort', "Invalid sort")
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
        listening = []

        # Todo: figure way to show shouts that are
        # - from users / pages listened to by the users [any country]
        # - from tags listened to by the user [only his country]

        # country = user.location.get('country')
        # if country:
        #     index_queryset = index_queryset.filter('term', country=country)

        # Listened Tags
        tags = user.listening2_tags_names
        if tags:
            listening_tags = Q('terms', tags=tags)
            listening.append(listening_tags)

        # Listened Users + user himself
        users = [user.pk] + user.listening2_pages_ids + user.listening2_users_ids
        if users:
            listening_users = Q('terms', uid=users)
            listening.append(listening_users)

        index_queryset = index_queryset.query('bool', should=listening)
        index_queryset = index_queryset.sort('-date_published')
        debug_logger.debug(index_queryset.to_dict())
        return index_queryset


class DiscoverItemFilter(filters.BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        if view.action != 'list':
            return queryset

        data = request.query_params
        country = data.get('country', '')
        country_queryset = queryset.filter(countries__contains=[country])
        no_country_queryset = queryset.filter(countries__contained_by=[''])
        if country != '' and country_queryset.count() != 0:
            queryset = country_queryset
        else:
            queryset = no_country_queryset
        return queryset


# Todo: check usage!
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
            raise InvalidParameter('type', "Should be `all`, `top` or `featured`")

        if value == 'featured':
            queryset = FeaturedTag.objects.all().order_by('rank')
            queryset = self.filter_location(queryset)
        return queryset

    def filter_category(self, queryset, value):
        tag_type = self.data.get('type')
        if tag_type == 'featured':
            raise InvalidParameter('category', "Does not work when type is `featured`")
        try:
            category = Category.objects.get(name=value)
            # return all tags that belong to the category except the main tag
            # todo: check if we really need to exclude the main tag or not
            # return queryset.filter(category=category).filter(~Q(id=category.main_tag_id))
            return queryset.filter(category=category)
        except Category.DoesNotExist:
            raise InvalidParameter('category', "Category '%s' does not exist" % value)

    def filter_country(self, queryset, value):
        tag_type = self.data.get('type')
        if tag_type not in ['top', 'featured']:
            raise InvalidParameter('country', "Only works when type equals `top` or `featured`")
        return queryset

    def filter_state(self, queryset, value):
        tag_type = self.data.get('type')
        if tag_type not in ['top', 'featured']:
            raise InvalidParameter('state', "Only works when type equals `top` or `featured`")
        return queryset

    def filter_city(self, queryset, value):
        tag_type = self.data.get('type')
        if tag_type not in ['top', 'featured']:
            raise InvalidParameter('city', "Only works when type equals `top` or `featured`")
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
