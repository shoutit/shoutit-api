# -*- coding: utf-8 -*-
"""

"""
from __future__ import unicode_literals

from rest_framework import permissions, viewsets, filters
from rest_framework.response import Response
from rest_framework.decorators import api_view, list_route, detail_route

from shoutit.controllers import user_controller

from shoutit.models import User
from shoutit.api.v2.serializers import UserSerializer, UserSerializer2
from shoutit.api.v2.permissions import IsOwnerOrReadOnly

from shoutit.api.renderers import render_user


class UserViewSet(viewsets.GenericViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    lookup_field = 'username'
    lookup_value_regex = '[0-9a-zA-Z.]{2,30}'
    serializer_class = UserSerializer2

    filter_backends = (filters.DjangoFilterBackend, filters.SearchFilter)
    filter_fields = ('id', 'username', 'email')
    search_fields = ('username', 'first_name', 'last_name', '=email')

    def get_queryset(self):
        return User.objects.all()

    def list(self, request, *args, **kwargs):
        """
        get users based on `filter_fields` and `search_fields`
        """
        users = self.filter_queryset(self.get_queryset())
        ret = {
            "results": [render_user(user) for user in users]
        }
        return Response(ret)

    def create(self, request, *args, **kwargs):
        return Response()

    def retrieve(self, request, *args, **kwargs):
        """
        get user
        """
        user = self.get_object()
        return Response(render_user(user, 5, request.user == user))

    def update(self, request, *args, **kwargs):
        """
        modify user
        """
        user = self.get_object()
        return Response(render_user(user, 5, request.user == user))

    def destroy(self, request,  *args, **kwargs):
        """
        delete user and everything attached to him
        """
        return Response()

    @detail_route(methods=['get', 'put'])
    def location(self, request, *args, **kwargs):
        """
        get or modify user location
        """
        return Response()

    @detail_route(methods=['get', 'put'])
    def image(self, request, *args, **kwargs):
        """
        get or modify user image
        """
        return Response()

    @detail_route(methods=['get', 'put', 'delete'])
    def video(self, request, *args, **kwargs):
        """
        get, modify or delete user video
        """
        return Response()

    @detail_route(methods=['get', 'put', 'delete'])
    def push(self, request, *args, **kwargs):
        """
        get, modify or delete user push tokens
        """
        return Response()

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

    @detail_route(methods=['get'])
    def listening(self, request, *args, **kwargs):
        """
        get user listening
        """
        return Response()
