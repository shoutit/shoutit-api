# -*- coding: utf-8 -*-
"""

"""
from __future__ import unicode_literals

from rest_framework import permissions, viewsets
from rest_framework.response import Response
from rest_framework.decorators import api_view, list_route

from shoutit.models import User
from shoutit.api.v2.permissions import IsOwnerOrReadOnly


class MiscViewSet(viewsets.ViewSet):
    """
    Other API Resources
    """
    @list_route(methods=['post'])
    def upload_shout_image(self, request):
        """
        Upload shout image
        """
        return Response({'hello': 'DRF!'})

    @list_route(methods=['get'])
    def currencies(self, request):
        """
        Get currencies
        """
        return Response({'hello': 'DRF!'})

    @list_route(methods=['get'])
    def categories(self, request):
        """
        Get categories
        """
        return Response({'hello': 'DRF!'})
