# -*- coding: utf-8 -*-
"""

"""
import math
from collections import OrderedDict

from django.conf import settings
from django.core.paginator import Paginator as DjangoPaginator
from django.utils.translation import ugettext_lazy as _
from elasticsearch import ElasticsearchException, SerializationError
from elasticsearch_dsl.result import Result
from rest_framework.pagination import CursorPagination
from rest_framework.pagination import PageNumberPagination, _positive_int
from rest_framework.response import Response
from rest_framework.templatetags.rest_framework import replace_query_param
from rest_framework.utils.urls import remove_query_param

from common.utils import utcfromtimestamp
from shoutit.api.v3.exceptions import InvalidParameter
from shoutit.utils import error_logger, debug_logger
from ..api_utils import get_current_uri


class DateTimePagination(CursorPagination):
    recent_on_top = False
    datetime_attribute = 'created_at'
    datetime_unix_attribute = 'created_at_unix'
    before_field = 'before'
    after_field = 'after'
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = settings.DEFAULT_MAX_PAGE_SIZE
    display_page_controls = True

    def paginate_queryset(self, queryset, request, view=None):
        """
        Paginate a queryset using unix timestamp query params.
        """
        self.page_size = self.get_page_size(request)

        before_query_param = request.query_params.get(self.before_field)
        after_query_param = request.query_params.get(self.after_field)
        if before_query_param and after_query_param:
            msg = _("Using '%(before)s' and '%(after)s' query params together is not allowed") % {
                'before': self.before_field, 'after': self.after_field}
            raise InvalidParameter('', msg)

        if before_query_param:
            try:
                filters = {
                    self.datetime_attribute + '__lt': utcfromtimestamp(int(before_query_param) - 1)
                }
                queryset = queryset.filter(**filters).order_by('-' + self.datetime_attribute)

            except (TypeError, ValueError):
                raise InvalidParameter(self.before_field, _("Should be a valid timestamp"))
        elif after_query_param:
            try:
                filters = {
                    self.datetime_attribute + '__gt': utcfromtimestamp(int(after_query_param) + 1)
                }
                queryset = queryset.filter(**filters).order_by(self.datetime_attribute)
            except (TypeError, ValueError):
                raise InvalidParameter(self.after_field, _("Should be a valid timestamp"))
        else:
            queryset = queryset.order_by('-' + self.datetime_attribute)

        paginator = DjangoPaginator(queryset, self.page_size)
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
        if not recent_object or len(self.page) < self.page_size:
            return None
        recent_object_timestamp = getattr(recent_object, self.datetime_unix_attribute)
        url = get_current_uri(self.request)
        url = replace_query_param(url, self.after_field, recent_object_timestamp)
        url = replace_query_param(url, self.page_size_query_param, self.page_size)
        return url

    def get_previous_link(self):
        oldest_object = hasattr(self, 'page') and len(self.page) and self.page[self.get_oldest_index()]
        if not oldest_object or len(self.page) < self.page_size:
            return None
        oldest_object_timestamp = getattr(oldest_object, self.datetime_unix_attribute)
        url = get_current_uri(self.request)
        url = replace_query_param(url, self.before_field, oldest_object_timestamp)
        url = replace_query_param(url, self.page_size_query_param, self.page_size)
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
    max_page_size = settings.DEFAULT_MAX_PAGE_SIZE
    results_field = 'results'
    show_count = True

    def get_paginated_response(self, data):
        res = [
            ('next', self.get_next_link()),
            ('previous', self.get_previous_link()),
            (self.results_field, data)
        ]
        if self.show_count:
            res.insert(0, ('count', self.page.paginator.count))
        return Response(OrderedDict(res))


class ShoutitPageNumberPaginationNoCount(ShoutitPageNumberPagination):
    show_count = False


class PageNumberIndexPagination(PageNumberPagination):
    page_size = 10
    page_number = 1
    page_size_query_param = 'page_size'
    max_page_size = settings.DEFAULT_MAX_PAGE_SIZE
    max_results = 1000
    results_field = 'results'
    template = 'rest_framework/pagination/previous_and_next.html'
    show_count = True

    # private
    _max_page_number_exceeded = False
    _max_possible_page_number_exceeded = False
    _num_results = 0
    _num_pages = 0

    def paginate_queryset(self, index_queryset, request, view=None):
        """
        Paginate a queryset using Elasticsearch index.
        """

        self.page_size = self.get_page_size(request)
        if not self.page_size:
            return None
        max_page_number = self.max_results / self.page_size
        page_number = request.query_params.get(self.page_query_param, 1)
        page_number = self.get_valid_page_number(page_number)

        index_response = []
        if page_number > max_page_number:
            self._max_page_number_exceeded = True
            self._num_results = index_queryset.count()
        else:
            _from = (page_number - 1) * self.page_size
            _to = page_number * self.page_size
            try:
                index_response = index_queryset[_from:_to].execute()
                # if there are no results for this [_from:_to], check if there are ones at all
                if not index_response:
                    self._num_results = index_queryset.count()
                    if self._num_results:
                        # there are results meaning provided page number exceeded max possible one
                        self._max_possible_page_number_exceeded = True
                else:
                    if isinstance(index_response[0], Result):
                        raise SerializationError("Results from different index")

                        # Logging success calls - to compare
                        # extra = {'request': request._request, 'query_dict': index_queryset.__dict__}
                        # error_logger.info('ES Success', extra=extra)

            except (ElasticsearchException, KeyError) as e:
                msg = "ES Exception: " + str(type(e))
                extra = {'detail': str(e), 'request': request._request, 'query_dict': index_queryset.__dict__}
                error_logger.warn(msg, exc_info=True, extra=extra)
                # possible errors
                # SerializationError: returned data was corrupted
                # KeyError: some bug in the elasticsearch-dsl library.
                # ConnectionTimeout
                # todo: handle returned data are from different index! report bug issue
                index_response = []

        # Save the index order. `None` is used to later filter out the objects that do not exist in db query
        index_tuples = [(s.meta.id, None) for s in index_response]
        objects_dict = OrderedDict(index_tuples)

        # Fetch objects from database
        ids = objects_dict.keys()
        if ids:
            qs = view.get_queryset().filter(id__in=ids)
        else:
            qs = []

        # Replace the values of objects_dict with the actual db objects and filter out the non existing ones
        # str(pk) is used to make sure the ids are converted to strings otherwise setitem will create new keys
        [objects_dict.__setitem__(str(s.pk), s) for s in qs]
        self.page = [o for o in objects_dict.values() if o]

        self._num_results = index_response.hits.total if self.page else 0
        self._num_pages = int(math.ceil(self._num_results / (self.page_size * 1.0)))
        if self._max_page_number_exceeded or self._max_possible_page_number_exceeded:
            self.page_number = min(self._num_pages + 1, max_page_number + 1)
        else:
            self.page_number = page_number
        self.request = request

        if (len(self.page) > 1 or self._num_results) and self.template is not None:
            # The browsable API should display pagination controls.
            self.display_page_controls = True
        return self.page

    def get_valid_page_number(self, page_number):
        try:
            page_number = int(page_number)
            if page_number <= 0:
                raise ValueError
        except ValueError:
            page_number = 1
        return page_number

    def get_paginated_response(self, data):
        res = [
            ('next', self.get_next_link()),
            ('previous', self.get_previous_link()),
            (self.results_field, data)
        ]
        if self.show_count:
            res.insert(0, ('count', self.fix_me(self._num_results)))
        if self._max_page_number_exceeded:
            res.insert(0, ('error', _('We do not return more than 1000 results for any query')))
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
        return self.page_number < self._num_pages

    def get_next_link(self):
        if not self.page_has_next():
            return None
        url = self.request.build_absolute_uri()
        url = replace_query_param(url, self.page_size_query_param, self.page_size)
        return replace_query_param(url, self.page_query_param, self.page_number + 1)

    def page_has_previous(self):
        if not (self.page or self._num_results):
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

    def fix_me(self, num):
        if 'profile' in self.request.query_params:
            return num
        try:
            if num <= 100:
                return num
            elif 100 < num < 300:
                return num * 2
            elif 300 < num:
                return num * 3
        except Exception as e:
            debug_logger.warn(str(e))
            return num
