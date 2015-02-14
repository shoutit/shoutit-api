# -*- coding: utf-8 -*-
"""

"""
from __future__ import unicode_literals

from django.conf.urls import url

from rest_framework.authtoken import views

from shoutit.api.v2.views import user_views


urlpatterns = [
    url(r'^token-auth/', views.obtain_auth_token),

    url(r'^users/$', user_views.ListUsers.as_view()),

    # url(r'^tags/$', user_views.ListUsers.as_view()),

    # url(r'^shouts/$', user_views.ListUsers.as_view()),

    url(r'^messages/(?P<mo>.)/$', user_views.view),
]
