"""

"""
from __future__ import unicode_literals

from django.contrib import admin

from shoutit.admin_utils import UserLinkMixin
from .models import CreditRule, CreditTransaction


@admin.register(CreditRule)
class CreditRuleAdmin(admin.ModelAdmin, UserLinkMixin):
    list_display = ('id', 'transaction_type', 'type', 'title', 'created_at', 'is_active')
    readonly_fields = ('created_at',)
    ordering = ('transaction_type', 'type')


@admin.register(CreditTransaction)
class CreditTransactionAdmin(admin.ModelAdmin, UserLinkMixin):
    list_display = ('id', '_user', 'type', 'amount', 'created_at', 'properties')
    search_fields = ('user__username',)
    raw_id_fields = ('user',)
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)
