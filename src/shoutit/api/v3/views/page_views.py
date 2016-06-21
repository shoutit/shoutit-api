# -*- coding: utf-8 -*-
"""

"""
from __future__ import unicode_literals

from django.views.decorators.cache import cache_control
from rest_framework import filters
from rest_framework.decorators import list_route
from rest_framework.response import Response

from common.constants import USER_TYPE_PAGE
from shoutit.api.v3.serializers import PageCategorySerializer
from shoutit.api.v3.views.profile_views import ProfileViewSet
from shoutit.models import User, PageCategory


class PageViewSet(ProfileViewSet):
    """
    Profile API Resource.
    """
    queryset = User.objects.filter(is_active=True, is_activated=True, type=USER_TYPE_PAGE).select_related('profile',
                                                                                                          'page')
    queryset_detail = User.objects.filter(is_active=True, type=USER_TYPE_PAGE).select_related('profile', 'page',
                                                                                              'linked_facebook',
                                                                                              'linked_gplus')
    filter_backends = (filters.DjangoFilterBackend, filters.SearchFilter)
    filter_fields = ('username', 'email', 'page__name')
    search_fields = ('=id', 'username', 'first_name', 'last_name', '=email', 'page__name')

    @cache_control(max_age=60 * 60 * 24)
    @list_route(methods=['get'], suffix='Categories')
    def categories(self, request):
        """
        List Pages Categories
        ---
        serializer: PageCategorySerializer
        """
        self.serializer_class = PageCategorySerializer
        categories = PageCategory.objects.root_nodes()
        serializer = self.get_serializer(categories, many=True)
        return Response(serializer.data)
