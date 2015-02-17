# -*- coding: utf-8 -*-
"""

"""
from __future__ import unicode_literals

from rest_framework import permissions, viewsets, filters
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.decorators import api_view, list_route, detail_route
from rest_framework_extensions.mixins import NestedViewSetMixin

from common.constants import USER_TYPE_INDIVIDUAL, USER_TYPE_BUSINESS
from shoutit.controllers import user_controller

from shoutit.models import User
from shoutit.api.v2.serializers import UserSerializer, UserSerializer2
from shoutit.api.v2.permissions import IsOwnerOrReadOnly

from shoutit.api.renderers import render_user, render_tag


class TagViewSet(viewsets.GenericViewSet):
    """
    API endpoint that allows tags to be viewed or interacted with.
    """
    lookup_field = 'id'
    lookup_value_regex = '[0-9a-zA-Z.]{2,30}'
    serializer_class = UserSerializer2

    filter_backends = (filters.DjangoFilterBackend, filters.SearchFilter)
    filter_fields = ('id', 'Name')
    search_fields = ('id', 'Name')

    def get_queryset(self):
        return User.objects.all()

    def list(self, request, *args, **kwargs):
        """
        get tags based on `filter_fields` and `search_fields`
        query params
            top:
            featured:
            search:
        """
        users = self.filter_queryset(self.get_queryset())
        ret = {
            "results": [render_user(user) for user in users]
        }
        return Response(ret)

    def retrieve(self, request, *args, **kwargs):
        """
        get tag
        """
        tag = self.get_object()
        return Response(render_tag(tag))

    @detail_route(methods=['get'])
    def shouts(self, request, *args, **kwargs):
        """
        get user shouts
        """
        return Response()

    @detail_route(methods=['post', 'delete'])
    def listen(self, request, *args, **kwargs):
        """
        start/stop listening to user
        """
        return Response()

    @detail_route(methods=['get'])
    def listeners(self, request, *args, **kwargs):
        """
        get user listeners
        """
        return Response()