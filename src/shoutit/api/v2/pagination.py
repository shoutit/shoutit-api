# -*- coding: utf-8 -*-
"""

"""
from __future__ import unicode_literals
from collections import OrderedDict
from django.core.paginator import InvalidPage, Paginator as DjangoPaginator
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.pagination import BasePagination, PageNumberPagination, _positive_int
from rest_framework.response import Response
from rest_framework.templatetags.rest_framework import replace_query_param
from datetime import datetime
from shoutit.api.api_utils import get_current_uri

from rest_framework.pagination import CursorPagination

# class NextPageByDateTimeField(serializers.Field):
#     """
#     Field that returns a link to the next page in time paginated results.
#     """
#
#     def to_representation(self, page):
#         view = self.context.get('view')
#         assert hasattr(view, 'datetime_unix_attribute'), "view '%s' has no 'datetime_unix_attribute'" % view
#         assert hasattr(view, 'after_field'), "view '%s' has no 'after_field'" % view
#         assert hasattr(view, 'paginate_by_param'), "view '%s' has no 'paginate_by_param'" % view
#
#         last_object = len(page) and page[-1]
#         if not last_object:
#             return None
#         last_object_timestamp = getattr(last_object, view.datetime_unix_attribute)
#         request = self.context.get('request')
#         url = request and get_current_uri(request) or ''
#         url = replace_query_param(url, view.after_field, last_object_timestamp)
#         url = replace_query_param(url, view.paginate_by_param, view.get_paginate_by())
#         return url
#
#
# class PreviousPageByDateTimeField(serializers.Field):
#     """
#     Field that returns a link to the previous page in time paginated results.
#     """
#
#     def to_representation(self, page):
#         view = self.context.get('view')
#         assert hasattr(view, 'datetime_unix_attribute'), "view '%s' has no 'datetime_unix_attribute'" % view
#         assert hasattr(view, 'after_field'), "view '%s' has no 'after_field'" % view
#         assert hasattr(view, 'paginate_by_param'), "view '%s' has no 'paginate_by_param'" % view
#
#         first_object = len(page) and page[0]
#         if not first_object:
#             return None
#         first_object_timestamp = getattr(first_object, view.datetime_unix_attribute)
#         request = self.context.get('request')
#         url = request and get_current_uri(request) or ''
#         url = replace_query_param(url, view.before_field, first_object_timestamp)
#         url = replace_query_param(url, view.paginate_by_param, view.get_paginate_by())
#         return url
#
#


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
                'detail': "Using '{}' and '{}' query params together is not allowed".format(self.before_field, self.after_field)
            })

        if before_query_param:
            try:
                filters = {
                    self.datetime_attribute + '__lt': datetime.fromtimestamp(int(before_query_param)-1)
                }
                queryset = queryset.filter(**filters).order_by('-' + self.datetime_attribute)

            except (TypeError, ValueError):
                raise ValidationError({self.before_field: "shout be a valid timestamp"})
        elif after_query_param:
            try:
                filters = {
                    self.datetime_attribute + '__gt': datetime.fromtimestamp(int(after_query_param)+1)
                }
                queryset = queryset.filter(**filters).order_by(self.datetime_attribute)
            except (TypeError, ValueError) as e:
                raise ValidationError({self.after_field: "shout be a valid timestamp"})
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
        recent_object = len(self.page) and self.page[self.get_recent_index()]
        if not recent_object:
            return None
        recent_object_timestamp = getattr(recent_object, self.datetime_unix_attribute)
        url = get_current_uri(self.request)
        url = replace_query_param(url, self.after_field, recent_object_timestamp)
        url = replace_query_param(url, self.page_size_query_param, self.get_page_size(self.request))
        return url

    def get_previous_link(self):
        oldest_object = len(self.page) and self.page[self.get_oldest_index()]
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

    def get_custom_shoutit_page_number_pagination_class(self, custom_page_size=None, custom_results_field=None):

        class PageNumberPaginationClass(ShoutitPageNumberPagination):
            page_size = custom_page_size or ShoutitPageNumberPagination.page_size
            results_field = custom_results_field or ShoutitPageNumberPagination.results_field

        return PageNumberPaginationClass
