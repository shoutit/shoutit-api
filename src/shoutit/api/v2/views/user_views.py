# -*- coding: utf-8 -*-
"""

"""
from __future__ import unicode_literals

from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.decorators import api_view

from shoutit.models import User


class ListUsers(APIView):
    """
    View to list all users in the system.

    * Requires token authentication.
    * Only admin users are able to access this view.
    """
    permission_classes = (permissions.IsAdminUser,)

    def get(self, request, format=None):
        """
        Return a list of all users.
        """
        usernames = [user.username for user in User.objects.all()]
        return Response(usernames)




@api_view(['GET'])
def view(request, mo):
    return Response({"message": "Hello for today! See you tomorrow!"})
