# -*- coding: utf-8 -*-
"""

"""
from __future__ import unicode_literals
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.pagination import DefaultObjectSerializer, BasePaginationSerializer
from rest_framework.templatetags.rest_framework import replace_query_param
from datetime import datetime
from shoutit.api.api_utils import get_current_uri


class NextPageByDateTimeField(serializers.Field):
    """
    Field that returns a link to the next page in time paginated results.
    """
    before_field = 'before'

    def to_representation(self, page):
        view = self.context.get('view')
        assert hasattr(view, 'datetime_unix_attribute'), "view '%s' has no 'datetime_unix_attribute'" % view
        first_object = len(page) and page[0]
        if not first_object:
            return None
        first_object_timestamp = getattr(first_object, view.datetime_unix_attribute)
        request = self.context.get('request')
        url = request and get_current_uri(request) or ''
        return replace_query_param(url, self.before_field, first_object_timestamp)


class PreviousPageByDateTimeField(serializers.Field):
    """
    Field that returns a link to the previous page in time paginated results.
    """
    after_field = 'after'

    def to_representation(self, page):
        view = self.context.get('view')
        assert hasattr(view, 'datetime_unix_attribute'), "view '%s' has no 'datetime_unix_attribute'" % view
        last_object = len(page) and page[-1]
        if not last_object:
            return None
        last_object_timestamp = getattr(last_object, view.datetime_unix_attribute)
        request = self.context.get('request')
        url = request and get_current_uri(request) or ''
        return replace_query_param(url, self.after_field, last_object_timestamp)


class TimePaginationSerializer(BasePaginationSerializer):
    """
    A custom implementation of a pagination serializer that uses DateTime.
    """
    next = NextPageByDateTimeField(source='*')
    previous = PreviousPageByDateTimeField(source='*')


class PaginationByDateTimeMixin(object):
    datetime_attribute = 'created_at'
    datetime_unix_attribute = 'created_at_unix'
    before_field = 'before'
    after_field = 'after'

    def paginate_queryset_by_time(self, queryset):
        """
        Paginate a queryset using timestamps.
        """
        page_size = self.get_paginate_by()
        if not page_size:
            return None

        before_query_param = self.request.query_params.get(self.before_field)
        after_query_param = self.request.query_params.get(self.after_field)
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

        paginator = self.paginator_class(queryset, page_size)
        page_number = 1
        page = paginator.page(page_number)
        # reverse the messages order inside the page itself if needed, so the results are always sorted from oldest to newest.
        if not after_query_param:
            page.object_list = page.object_list[::-1]
        return page
