# -*- coding: utf-8 -*-
"""

"""
from __future__ import unicode_literals

from django.conf.urls import url, include
from rest_framework import routers

from rest_framework.authtoken import views

from shoutit.api.v2.views import user_views, misc_views


# Routers provide an easy way of automatically determining the URL conf.
router = routers.DefaultRouter()
router.register(r'users', user_views.UserViewSet)
router.register(r'misc', misc_views.MiscViewSet, 'misc')
router.register(r'cat', misc_views.Categories, 'cat')


urlpatterns = [
    url(r'^', include(router.urls)),

    url(r'^token-auth/', views.obtain_auth_token),

    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')),



    # url(r'^tags/$', user_views.ListUsers.as_view()),

    # url(r'^shouts/$', user_views.ListUsers.as_view()),

    url(r'^messages/(?P<mo>.)/$', user_views.view),

]
