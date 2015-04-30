# -*- coding: utf-8 -*-
"""

"""
from __future__ import unicode_literals
from collections import OrderedDict
from django.core.paginator import Paginator as DjangoPaginator
from elasticsearch import ElasticsearchException
from rest_framework.exceptions import ValidationError
from rest_framework.pagination import PageNumberPagination, _positive_int
from rest_framework.response import Response
from rest_framework.templatetags.rest_framework import replace_query_param
from rest_framework.pagination import CursorPagination
from datetime import datetime
from rest_framework.utils.urls import remove_query_param
from shoutit.api.api_utils import get_current_uri
import math


class DateTimePagination(CursorPagination):
    recent_on_top = False
    datetime_attribute = 'created_at'
    datetime_unix_attribute = 'created_at_unix'
    before_field = 'before'
    after_field = 'after'
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100
    display_page_controls = True

    def paginate_queryset(self, queryset, request, view=None):
        """
        Paginate a queryset using unix timestamp query params.
        """
        page_size = self.get_page_size(request)
        if not page_size:
            return queryset

        before_query_param = request.query_params.get(self.before_field)
        after_query_param = request.query_params.get(self.after_field)
        if before_query_param and after_query_param:
            raise ValidationError({
                'detail': "Using '{}' and '{}' query params together is not allowed".format(
                    self.before_field, self.after_field)
            })

        if before_query_param:
            try:
                filters = {
                    self.datetime_attribute + '__lt': datetime.fromtimestamp(int(before_query_param) - 1)
                }
                queryset = queryset.filter(**filters).order_by('-' + self.datetime_attribute)

            except (TypeError, ValueError):
                raise ValidationError({self.before_field: "should be a valid timestamp"})
        elif after_query_param:
            try:
                filters = {
                    self.datetime_attribute + '__gt': datetime.fromtimestamp(int(after_query_param) + 1)
                }
                queryset = queryset.filter(**filters).order_by(self.datetime_attribute)
            except (TypeError, ValueError):
                raise ValidationError({self.after_field: "should be a valid timestamp"})
        else:
            queryset = queryset.order_by('-' + self.datetime_attribute)

        paginator = DjangoPaginator(queryset, page_size)
        page_number = 1
        page = paginator.page(page_number)
        # reverse the messages order inside the page itself if needed, so the results are always sorted from oldest to newest.
        # in both cases the object_list queryset should be converted to a list to maintain consistency.
        if not after_query_param:
            page.object_list = list(page.object_list)[::-1]
        else:
            page.object_list = list(page.object_list)

        # explicitly reverse the order if required
        if self.recent_on_top:
            page.object_list = list(page.object_list)[::-1]

        self.page = page
        self.request = request
        return self.page

    def get_recent_index(self):
        if self.recent_on_top:
            return 0
        return -1

    def get_oldest_index(self):
        if self.recent_on_top:
            return -1
        return 0

    def get_next_link(self):
        recent_object = hasattr(self, 'page') and len(self.page) and self.page[self.get_recent_index()]
        if not recent_object:
            return None
        recent_object_timestamp = getattr(recent_object, self.datetime_unix_attribute)
        url = get_current_uri(self.request)
        url = replace_query_param(url, self.after_field, recent_object_timestamp)
        url = replace_query_param(url, self.page_size_query_param, self.get_page_size(self.request))
        return url

    def get_previous_link(self):
        oldest_object = hasattr(self, 'page') and len(self.page) and self.page[self.get_oldest_index()]
        if not oldest_object:
            return None
        oldest_object_timestamp = getattr(oldest_object, self.datetime_unix_attribute)
        url = get_current_uri(self.request)
        url = replace_query_param(url, self.before_field, oldest_object_timestamp)
        url = replace_query_param(url, self.page_size_query_param, self.get_page_size(self.request))
        return url

    def get_page_size(self, request):
        if self.page_size_query_param:
            try:
                return _positive_int(
                    request.query_params[self.page_size_query_param],
                    strict=True,
                    cutoff=self.max_page_size
                )
            except (KeyError, ValueError):
                pass

        return self.page_size


class ReverseDateTimePagination(DateTimePagination):
    recent_on_top = True


class ReverseModifiedDateTimePagination(ReverseDateTimePagination):
    datetime_attribute = 'modified_at'
    datetime_unix_attribute = 'modified_at_unix'


class ShoutitPageNumberPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100
    results_field = 'results'

    def get_paginated_response(self, data):
        return Response(OrderedDict([
            ('count', self.page.paginator.count),
            ('next', self.get_next_link()),
            ('previous', self.get_previous_link()),
            (self.results_field, data)
        ]))


class ShoutitPaginationMixin(object):
    def get_custom_shoutit_page_number_pagination_class(self, custom_page_size=None,
                                                        custom_results_field=None):
        class PageNumberPaginationClass(ShoutitPageNumberPagination):
            page_size = custom_page_size or ShoutitPageNumberPagination.page_size
            results_field = custom_results_field or ShoutitPageNumberPagination.results_field

        return PageNumberPaginationClass


class DateTimeIndexPagination(DateTimePagination):
    datetime_attribute = 'date_published'
    datetime_unix_attribute = 'date_published_unix'

    def paginate_queryset(self, index_queryset, request, view=None):
        """
        Paginate a queryset using unix timestamp query params.
        """
        page_size = self.get_page_size(request)
        if not page_size:
            return index_queryset

        before_query_param = request.query_params.get(self.before_field)
        after_query_param = request.query_params.get(self.after_field)
        if before_query_param and after_query_param:
            raise ValidationError({
                'detail': "Using '{}' and '{}' query params together is not allowed".format(
                    self.before_field, self.after_field)
            })

        if before_query_param:
            try:
                filters = {
                    self.datetime_attribute: {'lt': datetime.fromtimestamp(int(before_query_param) - 1)}
                }
                index_queryset = index_queryset.filter('range', **filters).sort({self.datetime_attribute: 'desc'})

            except (TypeError, ValueError):
                raise ValidationError({self.before_field: "should be a valid timestamp"})
        elif after_query_param:
            try:
                filters = {
                    self.datetime_attribute: {'gt': datetime.fromtimestamp(int(after_query_param) + 1)}
                }
                index_queryset = index_queryset.filter('range', **filters).sort({self.datetime_attribute: 'asc'})
            except (TypeError, ValueError):
                raise ValidationError({self.after_field: "should be a valid timestamp"})
        else:
            index_queryset = index_queryset.sort({self.datetime_attribute: 'desc'})

        try:
            index_response = index_queryset[:page_size].execute()
        except ElasticsearchException:
            # todo: log!
            # possible errors
            # SerializationError: returned data was corrupted
            # ConnectionTimeout
            # https://elasticsearch-py.readthedocs.org/en/master/exceptions.html
            index_response = []

        object_ids = [object_index._id for object_index in index_response]
        page = view.model.objects.filter(id__in=object_ids) \
            .select_related(*view.select_related) \
            .prefetch_related(*view.prefetch_related) \
            .defer(*view.defer) \
            .order_by('-date_published')

        # reverse the objects order if needed, so the results are always sorted from oldest to newest.
        if not after_query_param:
            page = list(page)[::-1]
        else:
            page = list(page)

        # explicitly reverse the order if required
        if self.recent_on_top:
            page = page[::-1]

        self.request = request
        self.page = page
        return self.page


class ReverseDateTimeIndexPagination(DateTimeIndexPagination):
    recent_on_top = True


class PageNumberIndexPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 50
    max_results = 1000
    results_field = 'results'
    template = 'rest_framework/pagination/previous_and_next.html'

    def paginate_queryset(self, index_queryset, request, view=None):
        """
        Paginate a queryset using Elasticsearch index.
        """

        page_size = self.get_page_size(request)
        if not page_size:
            return None
        max_page_number = self.max_results / page_size
        page_number = request.query_params.get(self.page_query_param, 1)
        page_number = self.get_valid_page_number(page_number)

        if page_number > max_page_number:
            self.max_page_number_exceeded = True
            self.num_results = index_queryset.count()
            index_response = []
        else:
            _from = (page_number - 1) * page_size
            _to = page_number * page_size
            try:
                index_response = index_queryset[_from:_to].execute()
                # if there are no results for this [_from:_to], check if there are ones at all
                if not index_response:
                    self.num_results = index_queryset.count()
                    if self.num_results:
                        # there are results meaning provided page number exceeded max possible one
                        self.max_possible_page_number_exceeded = True
            except ElasticsearchException:
                # todo: log!
                # possible errors
                # SerializationError: returned data was corrupted
                # ConnectionTimeout
                # https://elasticsearch-py.readthedocs.org/en/master/exceptions.html
                index_response = []

        # save the order
        objects_dict = OrderedDict()
        for object_index in index_response:
            objects_dict[object_index._id] = None

        # populate from database
        ids = objects_dict.keys()
        if ids:
            qs = view.model.objects.filter(id__in=ids) \
                .select_related(*view.select_related) \
                .prefetch_related(*view.prefetch_related) \
                .defer(*view.defer)
        else:
            qs = []

        # sort populated objects according to saved order
        for shout in qs:
            objects_dict[shout.pk] = shout
        page = [item for key, item in objects_dict.items() if item]

        if (len(page) > 1 or (getattr(self, 'num_results', 0))) and self.template is not None:
            # The browsable API should display pagination controls.
            self.display_page_controls = True

        self.page = page
        if not hasattr(self, 'num_results'):
            self.num_results = index_response.hits.total if self.page else 0
        self.num_pages = int(math.ceil(self.num_results / (page_size * 1.0)))
        if getattr(self, 'max_page_number_exceeded', False) \
                or getattr(self, 'max_possible_page_number_exceeded', False):
            self.page_number = min(self.num_pages + 1, max_page_number + 1)
        else:
            self.page_number = page_number
        self.page_size = page_size
        self.request = request
        return self.page

    def get_valid_page_number(self, page_number):
        try:
            page_number = int(page_number)
            if page_number == 0:
                raise ValueError
        except ValueError:
            page_number = 1
        return page_number

    def get_paginated_response(self, data):
        res = [
            ('count', self.num_results),
            ('next', self.get_next_link()),
            ('previous', self.get_previous_link()),
            (self.results_field, data)
        ]
        if getattr(self, 'max_page_number_exceeded', False):
            res.insert(0, ('error', 'We do not return more than 1000 results for any query.'))
        return Response(OrderedDict(res))

    def get_page_size(self, request):
        if self.page_size_query_param:
            try:
                return _positive_int(
                    request.query_params[self.page_size_query_param],
                    strict=True,
                    cutoff=self.max_page_size
                )
            except (KeyError, ValueError):
                pass

        return self.page_size

    def get_html_context(self):
        return {
            'previous_url': self.get_previous_link(),
            'next_url': self.get_next_link()
        }

    def page_has_next(self):
        if not self.page:
            return None
        return self.page_number < self.num_pages

    def get_next_link(self):
        if not self.page_has_next():
            return None
        url = self.request.build_absolute_uri()
        url = replace_query_param(url, self.page_size_query_param, self.page_size)
        return replace_query_param(url, self.page_query_param, self.page_number + 1)

    def page_has_previous(self):
        if not (self.page or self.num_results):
            return None
        return self.page_number > 1

    def get_previous_link(self):
        if not self.page_has_previous():
            return None
        url = self.request.build_absolute_uri()
        if self.page_number == 2:
            return remove_query_param(url, self.page_query_param)
        url = replace_query_param(url, self.page_size_query_param, self.page_size)
        return replace_query_param(url, self.page_query_param, self.page_number - 1)
