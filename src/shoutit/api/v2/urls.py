# -*- coding: utf-8 -*-
"""

"""
from __future__ import unicode_literals

from django.conf.urls import url, include
from rest_framework import routers

from shoutit.api.v2.authentication import AccessTokenView
from shoutit.api.v2.views import user_views, misc_views, message_views, shout_views, notification_views


class ShoutitRouter(routers.DefaultRouter):
    include_format_suffixes = False

# Routers provide an easy way of automatically determining the URL conf.
router = ShoutitRouter(trailing_slash=False)
# router.register('shouts', shout_views.ShoutViewSet, 'shout')
router.register('users', user_views.UserViewSet, 'user')
# router.register('_users', user_views._UserViewSet, '_user')
# router.register('conversations', message_views.ConversationViewSet, 'conversation')
# router.register('messages', message_views.MessageViewSet, 'message')
# router.register('notifications', notification_views.NotificationViewSet, 'notification')
# router.register('tags', user_views.UserViewSet, 'tag')
# router.register(r'misc', misc_views.MiscViewSet, 'misc')

urlpatterns = (
    url(r'^', include(router.urls)),

    url(r'^oauth2/access_token$', AccessTokenView.as_view(), name='access_token'),

    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')),

    url(r'^docs/', include('rest_framework_swagger.urls')),
)
