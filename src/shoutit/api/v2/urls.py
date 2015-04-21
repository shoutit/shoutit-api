# -*- coding: utf-8 -*-
"""

"""
from __future__ import unicode_literals

from django.conf.urls import url, include
from rest_framework import routers

from shoutit.api.v2.authentication import AccessTokenView, ShoutitAuthView
from shoutit.api.v2.views import user_views, misc_views, message_views, shout_views, notification_views, tag_views


class ShoutitRouter(routers.DefaultRouter):
    include_format_suffixes = False

# Routers provide an easy way of automatically determining the URL conf.
router = ShoutitRouter(trailing_slash=False)
router.register('users', user_views.UserViewSet, 'user')
router.register('tags', tag_views.TagViewSet, 'tag')
router.register('shouts', shout_views.ShoutViewSet, 'shout')
router.register('conversations', message_views.ConversationViewSet, 'conversation')
router.register('messages', message_views.MessageViewSet, 'message')
router.register('notifications', notification_views.NotificationViewSet, 'notification')
router.register(r'misc', misc_views.MiscViewSet, 'misc')
router.register(r'auth', ShoutitAuthView, 'shoutit_auth')

urlpatterns = (
    url(r'^oauth2/access_token$', AccessTokenView.as_view(), name='access_token'),
    url(r'^docs/', include('rest_framework_swagger.urls')),
    url(r'^', include(router.urls)),
)
