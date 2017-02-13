"""

"""
from django.contrib import admin

from shoutit.admin_utils import UserLinkMixin
from .models import VideoClient


@admin.register(VideoClient)
class VideoClientAdmin(admin.ModelAdmin, UserLinkMixin):
    list_display = ('id', '_user', 'ttl', 'created_at', 'expires_at')
    search_fields = ('user__username',)
    readonly_fields = ('user', '_user', 'ttl', 'expires_at_unix', 'created_at', 'expires_at')
    ordering = ('-created_at',)
