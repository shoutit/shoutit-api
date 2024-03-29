# -*- coding: utf-8 -*-
"""

"""
from collections import OrderedDict

import django_filters
from django.conf import settings
from django.db.models import Q as DQ
from elasticsearch_dsl import Search, Q
from pydash import parse_int, arrays
from rest_framework import filters
from rest_framework.exceptions import ValidationError

from common.constants import COUNTRIES, TAG_TYPE_STR, TAG_TYPE_INT
from common.utils import process_tags
from shoutit.models import Category, Tag, PredefinedCity, FeaturedTag, DiscoverItem, User
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
            except DiscoverItem.DoesNotExist:
                raise ValidationError({'discover': ["Discover Item with id '%s' does not exist" % discover]})
            else:
                data.update(discover_item.shouts_query)

        # Filter shouts by user id if user username or id are passed in `user` query param
        user = data.get('user')
        if user:
            try:
                user_id = User.objects.get(username=user).pk
            except User.DoesNotExist:
                raise ValidationError({'user': ["User with username '%s' does not exist" % user]})
            else:
                index_queryset = index_queryset.filter('term', uid=user_id)

        # Exclude ids
        exclude_ids = data.get('exclude_ids')
        if isinstance(exclude_ids, str):
            exclude_ids = exclude_ids.split(',')
        if exclude_ids and not isinstance(exclude_ids, list):
            exclude_ids = [exclude_ids]
        if exclude_ids:
            exclude_ids = [str(i) for i in exclude_ids]
            index_queryset = index_queryset.filter(~Q('terms', _id=exclude_ids))

        # Shout type
        shout_type = data.get('shout_type')
        if shout_type:
            if shout_type not in ['all', 'offer', 'request']:
                raise ValidationError({'shout_type': ["Should be `all`, `request` or `offer`"]})
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
        country = data.get('country', '').upper()
        if country and country != 'all':
            index_queryset = index_queryset.filter('term', country=country)
            # todo: add state
            city = data.get('city')
            if city and city != 'all':
                # todo: use other means of finding the surrounding cities like state.
                try:
                    pd_city = PredefinedCity.objects.filter(city=city, country=country)[0]
                except IndexError:
                    pass
                else:
                    nearby_cities = pd_city.get_cities_within(settings.NEARBY_CITIES_RADIUS_KM)
                    cities = [nc.city for nc in nearby_cities]
                    cities.append(city)
                    cities = arrays.uniq(cities)
                    index_queryset = index_queryset.filter('terms', city=cities)

        latlng_errors = OrderedDict()
        down_left_lat = data.get('down_left_lat')
        down_left_lng = data.get('down_left_lng')
        up_right_lat = data.get('up_right_lat')
        up_right_lng = data.get('up_right_lng')
        try:
            if down_left_lat:
                down_left_lat = float(down_left_lat)
                if down_left_lat > float(up_right_lat) or not (90 >= down_left_lat >= -90):
                    latlng_errors['down_left_lat'] = [
                        "should be between -90 and 90, also not greater than 'up_right_lat'"]
                    index_queryset = index_queryset.filter('range', **{'latitude': {'gte': down_left_lat}})
            if down_left_lng:
                down_left_lng = float(down_left_lng)
                if down_left_lng > float(up_right_lng) or not (180 >= down_left_lng >= -180):
                    latlng_errors['down_left_lng'] = [
                        "should be between -180 and 180, also not greater than 'up_right_lng'"]
                index_queryset = index_queryset.filter('range', **{'longitude': {'gte': down_left_lng}})
            if up_right_lat:
                if not (90 >= float(up_right_lat) >= -90):
                    latlng_errors['up_right_lat'] = ["should be between -90 and 90"]
                index_queryset = index_queryset.filter('range', **{'latitude': {'lte': up_right_lat}})
            if up_right_lng:
                if not (180 >= float(up_right_lng) >= -180):
                    latlng_errors['up_right_lng'] = ["should be between -180 and 180"]
                index_queryset = index_queryset.filter('range', **{'longitude': {'lte': up_right_lng}})
        except ValueError:
            latlng_errors['error'] = ["invalid lat or lng parameters"]
        if latlng_errors:
            raise ValidationError(latlng_errors)

        # Category and Filters
        category = data.get('category')
        if category and category != 'all':
            try:
                category = Category.objects.prefetch_related('filters').get(DQ(name=category) | DQ(slug=category))
            except Category.DoesNotExist:
                raise ValidationError({'category': ["Category with name or slug '%s' does not exist" % category]})
            else:
                data['category'] = category.slug
                index_queryset = index_queryset.filter('terms', category=[category.name, category.slug])
                cat_filters = category.filters.values_list('slug', 'values_type')
                for cat_f_slug, cat_f_type in cat_filters:
                    if cat_f_type == TAG_TYPE_STR:
                        cat_f_param = data.get(cat_f_slug)
                        if cat_f_param:
                            index_queryset = index_queryset.filter('term', **{'filters__%s' % cat_f_slug: cat_f_param})
                    elif cat_f_type == TAG_TYPE_INT:
                        for m1, m2 in [('min', 'gte'), ('max', 'lte')]:
                            cat_f_param = data.get('%s_%s' % (m1, cat_f_slug))
                            if cat_f_param:
                                index_queryset = index_queryset.filter('range',
                                                                       **{'filters__%s' % cat_f_slug: {m2: cat_f_param}})

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
            None: ('-published_at',),
            'time': ('-published_at',),
            'price_asc': ('price',),
            'price_desc': ('-price',),
        }
        if sort and sort not in sort_types:
            raise ValidationError({'sort': ["Invalid sort"]})
        # selected_sort = ('-priority',) + sort_types[sort]
        selected_sort = sort_types[sort]
        if search:
            selected_sort = ('_score',) + selected_sort
        index_queryset = index_queryset.sort(*selected_sort)

        debug_logger.debug(index_queryset.to_dict())
        index_queryset.search_data = {
            k: parse_int(v, 10) or v for k, v in data.items()
        }
        return index_queryset


class HomeFilterBackend(filters.BaseFilterBackend):
    def filter_queryset(self, request, index_queryset, view):
        user = view.get_object()
        data = request.query_params
        listening = []

        # Listened Tags
        tags = user.listening2_tags_names
        if tags:
            country = user.location.get('country')
            listening_tags = Q('terms', tags=tags) & Q('term', country=country)
            listening.append(listening_tags)

        # Listened Profiles + user himself
        users = [user.pk] + user.listening2_pages_ids + user.listening2_users_ids
        if users:
            users = [str(u) for u in users]
            listening_users = Q('terms', uid=users)
            listening.append(listening_users)

        index_queryset = index_queryset.query('bool', should=listening)

        # Sort
        sort = data.get('sort')
        sort_types = {
            None: ('-published_at',),
            'time': ('-published_at',),
            'price_asc': ('price',),
            'price_desc': ('-price',),
        }
        if sort and sort not in sort_types:
            raise ValidationError({'sort': ["Invalid sort"]})
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
        country = data.get('country', '').upper()
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
            raise ValidationError({'type': ["Should be `all`, `top` or `featured`"]})

        if value == 'featured':
            queryset = FeaturedTag.objects.all().order_by('rank')
            queryset = self.filter_location(queryset)
        return queryset

    def filter_category(self, queryset, value):
        tag_type = self.data.get('type')
        if tag_type == 'featured':
            raise ValidationError({'category': ["does not work when type is `featured`"]})
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
            raise ValidationError({'country': ["only works when type equals `top` or `featured`"]})
        return queryset

    def filter_state(self, queryset, value):
        tag_type = self.data.get('type')
        if tag_type not in ['top', 'featured']:
            raise ValidationError({'state': ["only works when type equals `top` or `featured`"]})
        return queryset

    def filter_city(self, queryset, value):
        tag_type = self.data.get('type')
        if tag_type not in ['top', 'featured']:
            raise ValidationError({'city': ["only works when type equals `top` or `featured`"]})
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
            error_logger.warn("Discover returned 0 Featured Tags", extra={
                'country': country, 'state': state, 'city': city,
            })
        return queryset
