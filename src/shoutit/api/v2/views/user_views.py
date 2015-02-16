# -*- coding: utf-8 -*-
"""

"""
from __future__ import unicode_literals

from rest_framework import permissions, viewsets, filters
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.decorators import api_view, list_route
from rest_framework_extensions.mixins import NestedViewSetMixin

from common.constants import USER_TYPE_INDIVIDUAL, USER_TYPE_BUSINESS
from shoutit.controllers import user_controller

from shoutit.models import User
from shoutit.api.v2.serializers import UserSerializer, UserSerializer2
from shoutit.api.v2.permissions import IsOwnerOrReadOnly

from shoutit.api.renderers import render_user


class UserViewSet(NestedViewSetMixin, viewsets.ModelViewSet):
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
        return list of users based on query args
        """
        users = self.filter_queryset(self.get_queryset())
        ret = {
            "results": [render_user(user) for user in users]
        }
        return Response(ret)

    def create(self, request, *args, **kwargs):
        return Response()

    def retrieve(self, request, username, *args, **kwargs):
        """
        return specific user using his username
        """
        user = self.get_object()
        return Response(render_user(user, 5, request.user == user))

    def update(self, request, username, *args, **kwargs):
        """
        update user attributes
        """
        return Response()

    def destroy(self, request, username, *args, **kwargs):
        """
        delete user and everything attached to him
        """
        return Response()


class ListUsers(APIView):
    """
    View to list all users in the system.

    * Requires token authentication.
    * Only admin users are able to access this view.
    """
    permission_classes = (permissions.IsAdminUser, IsOwnerOrReadOnly)

    def get(self, request, format=None):
        """
        Return a list of all users.
        """
        usernames = [user.username for user in User.objects.all()]
        return Response(usernames)




@api_view(['GET'])
def view(request, mo):
    return Response({"message": "Hello for today! See you tomorrow!"})
