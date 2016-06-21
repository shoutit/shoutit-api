# -*- coding: utf-8 -*-
"""

"""
from __future__ import unicode_literals

from django.views.decorators.cache import cache_control
from rest_framework import filters
from rest_framework.decorators import list_route, detail_route
from rest_framework.response import Response

from common.constants import USER_TYPE_PAGE
from shoutit.api.v3.filters import ProfileFilter
from shoutit.models import User, PageCategory
from ..serializers import (PageCategorySerializer, ProfileSerializer, ProfileDetailSerializer, MessageSerializer, TagDetailSerializer,
                           ProfileDeactivationSerializer, GuestSerializer, ProfileLinkSerializer,
                           ProfileContactsSerializer)
from ..views.profile_views import ProfileViewSet


class PageViewSet(ProfileViewSet):
    """
    Profile API Resource.
    """
    queryset = User.objects.filter(is_active=True, is_activated=True, type=USER_TYPE_PAGE).select_related('page')
    queryset_detail = User.objects.filter(is_active=True, type=USER_TYPE_PAGE).select_related('page')
    filter_backends = (ProfileFilter, filters.SearchFilter)
    search_fields = ('=id', '=email', 'username', 'page__name')

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

    @detail_route(methods=['get'], suffix='Page Admins')
    def admins(self, request, *args, **kwargs):
        """
        List the Page admins
        Returned list is profiles of type `user`
        ###Response
        <pre><code>
        {
          "next": null, // next results page url
          "previous": null, // previous results page url
          "results": [] // list of {ProfileSerializer}
        }
        </code></pre>
        ---
        serializer: ProfileSerializer
        omit_parameters:
            - form
        parameters:
            - name: username
              description: me for logged in page
              paramType: path
              required: true
              defaultValue: me
            - name: page
              paramType: query
            - name: page_size
              paramType: query
        """
        self.serializer_detail_class = ProfileSerializer
        page = self.get_object().page
        admins = page.admins.all()
        page = self.paginate_queryset(admins)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)
