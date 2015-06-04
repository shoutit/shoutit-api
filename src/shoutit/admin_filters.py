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
        # from DateFieldListFilter constructor
        now = timezone.now()
        if timezone.is_aware(now):
            now = timezone.localtime(now)
        if isinstance(field, DateTimeField):
            today = now.replace(hour=0, minute=0, second=0, microsecond=0)
        else:  # field is a models.DateField
            today = now.date()

        # convert the links tuple to list to be able to insert elements in it
        links_list = list(self.links)

        # 1 to 7 days ago
        for day in range(1, 8):
            day_ago = today + datetime.timedelta(days=-day)
            after_day_ago = day_ago + datetime.timedelta(days=+1)
            label = 'Yesterday' if day == 1 else '%s days ago [%s]' % (day, day_ago.strftime('%Y-%m-%d'))
            day_ago_link = (label, {
                self.lookup_kwarg_since: str(day_ago),
                self.lookup_kwarg_until: str(after_day_ago),
            })
            links_list.insert(day + 1, day_ago_link)

        # convert back to tuple
        self.links = tuple(links_list)
