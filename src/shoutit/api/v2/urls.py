# -*- coding: utf-8 -*-
"""

"""
from __future__ import unicode_literals

from django.conf.urls import url, include
from rest_framework import routers
from rest_framework_extensions.routers import NestedRouterMixin

from rest_framework.authtoken import views
from shoutit.api.v2.authentication import AccessTokenView

from shoutit.api.v2.views import user_views, misc_views


class ShoutitRouter(NestedRouterMixin, routers.DefaultRouter):
    pass

# Routers provide an easy way of automatically determining the URL conf.
router = ShoutitRouter()
router.register(r'users', user_views.UserViewSet, 'user')
router.register(r'tags', user_views.UserViewSet, 'tag')
router.register(r'shouts', user_views.UserViewSet, 'shout')

conversation_router = router.register(r'conversation', user_views.UserViewSet, 'conversation')
conversation_router.register(r'messages', user_views.UserViewSet, 'conversation-message', ['conversations'])

router.register(r'misc', misc_views.MiscViewSet, 'misc')
router.register(r'cat', misc_views.Categories, 'cat')


urlpatterns = [
    url(r'^', include(router.urls)),

    url(r'^token-auth/', views.obtain_auth_token),

    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')),


    url('^oauth2/access_token/?$', AccessTokenView.as_view(), name='access_token'),

    url(r'^messages/(?P<mo>.)/$', user_views.view),

]
