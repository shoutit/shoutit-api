# -*- coding: utf-8 -*-
"""

"""
from __future__ import unicode_literals

from rest_framework import permissions, viewsets
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework.views import APIView
from rest_framework.decorators import api_view, list_route

from shoutit.models import User
from shoutit.api.v2.serializers import UserSerializer
from shoutit.api.v2.permissions import IsOwnerOrReadOnly


class MiscViewSet(viewsets.ViewSet):
    """
    Other calls to retrieve extra stuff
    """

    def list(self, request):
        return Response({
            'hello': reverse('misc-hello', request=request)
        })

    @list_route(methods=['get', 'post', 'put'])
    def hello(self, request):
        """
        hi there!
        :param request:
        :return:
        """
        return Response({'hello': 'DRF!'})


class Categories(APIView):
    def get(self, request):
        return Response({'hello': 'man!'})
