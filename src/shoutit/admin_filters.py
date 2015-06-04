# -*- coding: utf-8 -*-
"""

"""
from __future__ import unicode_literals
import datetime
from django.contrib import admin
from django.contrib.admin import DateFieldListFilter
from django.db.models import Q, DateTimeField
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from shoutit.models import User, Profile


class UserEmailFilter(admin.SimpleListFilter):
    # Human-readable title which will be displayed in the
    # right admin sidebar just above the filter options.
    title = _('with email')

    # Parameter for the filter that will be used in the URL query.
    parameter_name = 'with_email'

    def lookups(self, request, model_admin):
        return (
            ('shoutit', _('only shoutit users')),
            ('yes', _('yes')),
            ('no', _('no')),
            ('cl', _('only cl users')),
        )

    def queryset(self, request, queryset):
        if queryset.model == User:
            if self.value() == 'shoutit':
                return queryset.filter(~Q(email=''), ~Q(email__icontains='@sale.craigslist.org'))
            if self.value() == 'yes':
                return queryset.filter(~Q(email=''))
            if self.value() == 'no':
                return queryset.filter(email='')
            if self.value() == 'cl':
                return queryset.filter(email__icontains='@sale.craigslist.org')
        elif queryset.model == Profile:
            if self.value() == 'shoutit':
                return queryset.filter(~Q(user__email=''),
                                       ~Q(user__email__icontains='@sale.craigslist.org'))
            if self.value() == 'yes':
                return queryset.filter(~Q(user__email=''))
            if self.value() == 'no':
                return queryset.filter(user__email='')
            if self.value() == 'cl':
                return queryset.filter(user__email__icontains='@sale.craigslist.org')


class ShoutitDateFieldListFilter(DateFieldListFilter):
    def __init__(self, field, request, params, model, model_admin, field_path):
        super(ShoutitDateFieldListFilter, self).__init__(field, request, params, model, model_admin,
                                                         field_path)
        now = timezone.now()
        # When time zone support is enabled, convert "now" to the user's time
        # zone so Django's definition of "Today" matches what the user expects.
        if timezone.is_aware(now):
            now = timezone.localtime(now)

        if isinstance(field, DateTimeField):
            today = now.replace(hour=0, minute=0, second=0, microsecond=0)
        else:  # field is a models.DateField
            today = now.date()
        yesterday = today + datetime.timedelta(days=-1)

        yesterday_link = (_('Yesterday'), {
            self.lookup_kwarg_since: str(yesterday),
            self.lookup_kwarg_until: str(today),
        })
        links_list = list(self.links)
        links_list.insert(2, yesterday_link)
        self.links = tuple(links_list)
