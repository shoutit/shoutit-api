# -*- coding: utf-8 -*-
"""

"""
from __future__ import unicode_literals

from datetime import timedelta

from django.conf import settings
from django.db.models import Q
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from elasticsearch_dsl import Search, Q as EQ
from pydash import parse_int, arrays
from rest_framework import filters

from common.constants import TAG_TYPE_STR, TAG_TYPE_INT
from common.utils import process_tags
from shoutit.api.v3.exceptions import InvalidParameter
from shoutit.models import Category, PredefinedCity, DiscoverItem, User
from shoutit.utils import debug_logger


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
                raise InvalidParameter('discover', _("Invalid discover id"))
            except DiscoverItem.DoesNotExist:
                msg = _("Discover Item with id '%(discover)s' does not exist") % {'discover': discover}
                raise InvalidParameter('discover', msg)
            else:
                data.update(discover_item.shouts_query)

        # Filter shouts by user id if user username is passed in `profile` query param
        user = data.get('profile') or data.get('user')
        if user:
            # Replace `me` with logged in username
            if user == 'me' and request.user.is_authenticated():
                user = request.user.username

            # Get the user id using username
            try:
                user_id = str(User.objects.values('pk').get(username=user)['pk'])
            except User.DoesNotExist:
                msg = _("Profile with username '%(username)s' does not exist") % {'username': user}
                raise InvalidParameter('profile', msg)
            else:
                index_queryset = index_queryset.filter('term', uid=user_id)

            # When listing user's own shouts show him the expired ones
            if user == request.user.username:
                setattr(view, 'get_expired', True)

        # Exclude shouts using their ids
        exclude = data.get('exclude')
        if isinstance(exclude, basestring):
            exclude = exclude.split(',')
        if exclude and not isinstance(exclude, list):
            exclude = [exclude]
        if exclude:
            index_queryset = index_queryset.filter(~EQ('terms', _id=map(str, exclude)))

        # Shout type
        shout_type = data.get('shout_type')
        if shout_type:
            if shout_type not in ['all', 'offer', 'request']:
                msg = _("Should be `all`, `request` or `offer`")
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
                    cities = map(lambda nc: nc.city, nearby_cities)
                    cities.append(city)
                    cities = arrays.unique(cities)
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
                                           _("Should be between -90 and 90, also not greater than 'up_right_lat'"))
                index_queryset = index_queryset.filter('range', **{'latitude': {'gte': down_left_lat}})
            if down_left_lng:
                latlng_key = 'down_left_lng'
                down_left_lng = float(down_left_lng)
                up_right_lng = up_right_lng or 180
                if down_left_lng > float(up_right_lng) or not (180 >= down_left_lng >= -180):
                    raise InvalidParameter('down_left_lng',
                                           _("Should be between -180 and 180, also not greater than 'up_right_lng'"))
                index_queryset = index_queryset.filter('range', **{'longitude': {'gte': down_left_lng}})
            if up_right_lat:
                latlng_key = 'up_right_lat'
                if not (90 >= float(up_right_lat) >= -90):
                    raise InvalidParameter('up_right_lat', _("Should be between -90 and 90"))
                index_queryset = index_queryset.filter('range', **{'latitude': {'lte': up_right_lat}})
            if up_right_lng:
                latlng_key = 'up_right_lng'
                if not (180 >= float(up_right_lng) >= -180):
                    raise InvalidParameter('up_right_lng', _("Should be between -180 and 180"))
                index_queryset = index_queryset.filter('range', **{'longitude': {'lte': up_right_lng}})
        except ValueError:
            raise InvalidParameter(latlng_key, _("Invalid number"))

        # Category and Filters
        category = data.get('category')
        if category and category != 'all':
            try:
                category = Category.objects.prefetch_related('filters').get(slug=category)
            except Category.DoesNotExist:
                msg = _("Category with slug '%(slug)s' does not exist") % {'slug': category}
                raise InvalidParameter('category', msg)
            else:
                data['category'] = category.slug
                index_queryset = index_queryset.filter('terms', category=[category.name, category.slug])
                cat_filters = category.filters.values_list('slug', 'values_type')
                for cat_f_slug, cat_f_type in cat_filters:
                    if cat_f_type == TAG_TYPE_STR:
                        cat_f_param = data.get(cat_f_slug)
                        if cat_f_param:
                            cat_f_params = cat_f_param.split(',')
                            index_queryset = index_queryset.filter('terms',
                                                                   **{'filters__%s' % cat_f_slug: cat_f_params})
                    elif cat_f_type == TAG_TYPE_INT:
                        for m1, m2 in [('min', 'gte'), ('max', 'lte')]:
                            cat_f_param = data.get('%s_%s' % (m1, cat_f_slug))
                            if cat_f_param:
                                index_queryset = index_queryset.filter('range',
                                                                       **{'filters__%s' % cat_f_slug: {
                                                                           m2: cat_f_param}})

        # Price
        min_price = data.get('min_price')
        if min_price:
            index_queryset = index_queryset.filter('range', **{'price': {'gte': min_price}})

        max_price = data.get('max_price')
        if max_price:
            index_queryset = index_queryset.filter('range', **{'price': {'lte': max_price}})

        # Expired
        if not getattr(view, 'get_expired', False):
            now = timezone.now()
            min_published = now - timedelta(days=int(settings.MAX_EXPIRY_DAYS))

            # Recently published and no specified expires_at
            recently_published = EQ('range', **{'published_at': {'gte': min_published}})
            no_expiry_still_valid = EQ('bool', filter=[EQ('missing', field='expires_at'), recently_published])

            # Not expired
            not_expired = EQ('range', **{'expires_at': {'gte': now}})
            expiry_still_valid = EQ('bool', filter=[EQ('exists', field='expires_at'), not_expired])

            index_queryset = index_queryset.filter(no_expiry_still_valid | expiry_still_valid)

        # Sorting
        sort = data.get('sort')
        sort_types = {
            None: ('-published_at',),
            'time': ('-published_at',),
            'price_asc': ('price',),
            'price_desc': ('-price',),
        }
        if sort and sort not in sort_types:
            raise InvalidParameter('sort', _("Invalid sort"))
        # selected_sort = ('-priority',) + sort_types[sort]
        selected_sort = sort_types[sort]
        if search:
            selected_sort = ('_score',) + selected_sort
        index_queryset = index_queryset.sort(*selected_sort)

        debug_logger.debug(index_queryset.to_dict())
        index_queryset.search_data = {k: parse_int(v, 10) or v for k, v in data.items()}
        return index_queryset


class HomeFilterBackend(filters.BaseFilterBackend):
    def filter_queryset(self, request, index_queryset, view):
        user = request.user
        listening = []

        # Listened Tags
        tags = user.listening2_tags_names
        if tags:
            country = user.location.get('country')
            listening_tags = EQ('terms', tags=tags) & EQ('term', country=country)
            listening.append(listening_tags)

        # Listened Profiles + user himself
        profiles = [user.pk] + user.listening2_pages_ids + user.listening2_users_ids
        if profiles:
            listening_profiles = EQ('terms', uid=map(str, profiles))
            listening.append(listening_profiles)

        index_queryset = index_queryset.query('bool', should=listening)
        index_queryset = index_queryset.sort('-published_at')
        debug_logger.debug(index_queryset.to_dict())
        return index_queryset


class DiscoverItemFilter(filters.BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        if view.action != 'list':
            return queryset

        data = request.query_params
        country = data.get('country', '').upper()
        country_queryset = queryset.filter(countries__contains=[country])
        no_country_queryset = queryset.filter(countries__contained_by=[''])
        if country != '' and country_queryset.count() != 0:
            queryset = country_queryset
        else:
            queryset = no_country_queryset
        return queryset


class ProfileFilter(filters.BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        if view.action != 'list':
            return queryset

        data = request.query_params
        country = data.get('country', '').upper()
        if country:
            queryset = queryset.filter(Q(profile__country=country) | Q(page__country=country))
        return queryset
