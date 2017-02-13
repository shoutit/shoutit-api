"""

"""
from django.contrib import admin

from .models import PusherChannel, PusherChannelJoin


@admin.register(PusherChannel)
class PusherChannelAdmin(admin.ModelAdmin):
    list_display = ('name', 'type', 'users_count', 'created_at')
    search_fields = ('name', 'users__username')
    raw_id_fields = ('users',)
    ordering = ('-created_at',)


@admin.register(PusherChannelJoin)
class PusherChannelJoinAdmin(admin.ModelAdmin):
    list_display = ('channel', 'user', 'created_at')
    raw_id_fields = ('channel', 'user')
    search_fields = ('channel__name', 'user__username')
    ordering = ('-created_at',)
