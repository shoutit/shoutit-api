"""

"""
from __future__ import unicode_literals

from django.contrib import admin

from shoutit.admin_utils import UserLinkMixin
from .models import CreditRule, CreditTransaction, PromoteLabel


@admin.register(CreditRule)
class CreditRuleAdmin(admin.ModelAdmin, UserLinkMixin):
    list_display = ('id', 'transaction_type', 'type', 'name', 'created_at', 'is_active')
    readonly_fields = ('created_at',)
    ordering = ('transaction_type', 'type')


@admin.register(CreditTransaction)
class CreditTransactionAdmin(admin.ModelAdmin, UserLinkMixin):
    list_display = ('id', '_user', 'rule', 'amount', 'created_at', 'properties')
    search_fields = ('user__username',)
    raw_id_fields = ('user',)
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)


@admin.register(PromoteLabel)
class PromoteLabelAdmin(admin.ModelAdmin, UserLinkMixin):
    list_display = ('id', 'name', 'rank', 'color', 'bg_color', 'description', 'created_at')
    readonly_fields = ('created_at',)
    ordering = ('rank',)
