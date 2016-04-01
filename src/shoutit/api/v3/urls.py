# -*- coding: utf-8 -*-
"""

"""
from __future__ import unicode_literals

from django.conf.urls import url, include
from rest_framework import routers

from shoutit_pusher.views import ShoutitPusherViewSet
from shoutit_twilio.views import ShoutitTwilioViewSet
from .views import (user_views, misc_views, message_views, shout_views, notification_views, tag_views,
                    authentication_views, discover_views)


class ShoutitRouter(routers.DefaultRouter):
    include_format_suffixes = False


# Routers provide an easy way of automatically determining the URL conf.
router = ShoutitRouter(trailing_slash=False)
router.register('users', user_views.ProfileViewSet, 'user')
router.register('profiles', user_views.ProfileViewSet, 'profile')
router.register('tags', tag_views.TagViewSet, 'tag')
router.register('shouts', shout_views.ShoutViewSet, 'shout')
router.register('conversations', message_views.ConversationViewSet, 'conversation')
router.register('messages', message_views.MessageViewSet, 'message')
router.register('notifications', notification_views.NotificationViewSet, 'notification')
router.register('misc', misc_views.MiscViewSet, 'misc')
router.register('auth', authentication_views.ShoutitAuthViewSet, 'shoutit_auth')
router.register('pusher', ShoutitPusherViewSet, 'pusher')
router.register('twilio', ShoutitTwilioViewSet, 'twilio')
router.register('discover', discover_views.DiscoverViewSet, 'discover')

urlpatterns = [
    url(r'^oauth2/access_token$', authentication_views.AccessTokenView.as_view(), name='access_token'),
    url(r'^', include(router.urls)),
]
