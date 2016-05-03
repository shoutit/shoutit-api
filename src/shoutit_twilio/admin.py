"""

"""
from __future__ import unicode_literals

from django.contrib import admin

from .models import VideoClient


@admin.register(VideoClient)
class VideoClientAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'ttl', 'created_at')
    search_fields = ('user__username',)
    raw_id_fields = ('user',)
    ordering = ('-created_at',)
