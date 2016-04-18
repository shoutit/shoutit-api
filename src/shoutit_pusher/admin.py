"""

"""
from __future__ import unicode_literals

from django.contrib import admin

from .models import PusherChannel, PusherChannelJoin


@admin.register(PusherChannel)
class PusherChannelAdmin(admin.ModelAdmin):
    list_display = ('type', 'name')
    raw_id_fields = ('users',)


@admin.register(PusherChannelJoin)
class PusherChannelJoinAdmin(admin.ModelAdmin):
    list_display = ('channel', 'user')
    raw_id_fields = ('channel', 'user')
