# -*- coding: utf-8 -*-
"""

"""
from __future__ import unicode_literals

from django.views.decorators.cache import cache_control
from rest_framework import filters, mixins, viewsets
from rest_framework.decorators import list_route, detail_route
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework_extensions.mixins import DetailSerializerMixin

from common.constants import USER_TYPE_PAGE
from shoutit.api.v3.filters import ProfileFilter
from shoutit.api.v3.pagination import ShoutitPageNumberPaginationNoCount
from shoutit.models import User, PageCategory
from ..serializers import (PageCategorySerializer, ProfileSerializer, ProfileDetailSerializer, AddAdminSerializer, RemoveAdminSerializer,
                           CreatePageSerializer)


class PageViewSet(DetailSerializerMixin, mixins.ListModelMixin, mixins.CreateModelMixin, viewsets.GenericViewSet):
    """
    Profile API Resource.
    """
    lookup_field = 'username'
    lookup_value_regex = '[0-9a-zA-Z._]+'
    serializer_class = ProfileSerializer
    serializer_detail_class = ProfileDetailSerializer
    queryset = User.objects.filter(is_active=True, is_activated=True, type=USER_TYPE_PAGE).select_related('page')
    queryset_detail = User.objects.filter(is_active=True, type=USER_TYPE_PAGE).select_related('page')
    filter_backends = (ProfileFilter, filters.SearchFilter)
    search_fields = ('=id', '=email', 'username', 'page__name')
    pagination_class = ShoutitPageNumberPaginationNoCount
    permission_classes = (IsAuthenticatedOrReadOnly,)

    def get_object(self):
        username = self.kwargs.get(self.lookup_field)
        if self.request.user.is_authenticated() and self.request.user.type == USER_TYPE_PAGE:
            if username == 'me' or username == self.request.user.username:
                return self.request.user
        return super(PageViewSet, self).get_object()

    def list(self, request, *args, **kwargs):
        """
        List Pages based on `search` and `country` query params.

        ####These attributes are omitted
        `location.latitude`, `location.longitude`, `location.address`

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
        parameters:
            - name: search
              paramType: query
            - name: country
              paramType: query
        """
        return super(PageViewSet, self).list(request, *args, **kwargs)

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

    def create(self, request, *args, **kwargs):
        """
        Create a Page
        ###REQUIRES AUTH
        ###Request
        ####Body Example
        <pre><code>
        {
            "page_name": "New Page",
            "page_category": {
                "slug": "local-business"
            }
        }
        </code></pre>

        ---
        serializer: ProfileDetailSerializer
        omit_parameters:
            - form
        parameters:
            - name: body
              paramType: body
        """
        self.serializer_class = CreatePageSerializer
        return super(PageViewSet, self).create(request, *args, **kwargs)

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

    @detail_route(methods=['post', 'delete'], suffix='Add / Remove Admin')
    def admin(self, request, *args, **kwargs):
        """
        Add profile to / remove from the admins of this page
        ###REQUIRES AUTH
        The logged in profile should be admin in this page.
        ###Request
        ####Body
        <pre><code>
        {
            "profile": {
                "id": "id of the profile to be added to / removed from the admins of this page"
            }
        }
        </code></pre>
        ---
        omit_serializer: true
        omit_parameters:
            - form
        parameters:
            - name: body
              paramType: body
        """
        if request.method == 'POST':
            self.serializer_detail_class = AddAdminSerializer
        else:
            self.serializer_detail_class = RemoveAdminSerializer
        page = self.get_object().page
        serializer = self.get_serializer(instance=page, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
