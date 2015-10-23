# -*- coding: utf-8 -*-
"""

"""
from __future__ import unicode_literals

from django.conf.urls import url, include
from rest_framework import routers

from shoutit.api.v2.views import (user_views, misc_views, message_views, shout_views, notification_views, tag_views,
                                  sms_views, authentication_views)
from shoutit_pusher.views import ShoutitPusherViewSet


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
router.register('misc', misc_views.MiscViewSet, 'misc')
router.register('sms', sms_views.SMSViewSet, 'sms')
router.register('auth', authentication_views.ShoutitAuthViewSet, 'shoutit_auth')
router.register('pusher', ShoutitPusherViewSet, 'pusher')

urlpatterns = [
    url(r'^oauth2/access_token$', authentication_views.AccessTokenView.as_view(), name='access_token'),
    url(r'^docs/', include('rest_framework_swagger.urls')),
    url(r'^', include(router.urls)),
]
