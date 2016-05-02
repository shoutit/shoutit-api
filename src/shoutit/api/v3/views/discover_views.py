# -*- coding: utf-8 -*-
"""

"""
from __future__ import unicode_literals

from rest_framework import permissions, viewsets, mixins
from rest_framework_extensions.mixins import DetailSerializerMixin

from shoutit.models import DiscoverItem
from ..filters import DiscoverItemFilter
from ..pagination import ShoutitPageNumberPagination
from ..serializers import (DiscoverItemSerializer, DiscoverItemDetailSerializer)


class DiscoverViewSet(DetailSerializerMixin, mixins.RetrieveModelMixin, mixins.ListModelMixin, viewsets.GenericViewSet):
    """
    Discover API Resource.
    """
    serializer_class = DiscoverItemSerializer
    serializer_detail_class = DiscoverItemDetailSerializer
    pagination_class = ShoutitPageNumberPagination
    filter_backends = (DiscoverItemFilter,)
    permission_classes = (permissions.AllowAny,)

    def get_queryset(self):
        if self.action == 'list':
            return DiscoverItem.objects.filter(position=0)
        else:
            return DiscoverItem.objects.all()

    def list(self, request, *args, **kwargs):
        """
        List DiscoverItems based on `country` query param.
        ###Response
        <pre><code>
        {
          "count": 4, // number of results
          "next": null, // next results page url
          "previous": null, // previous results page url
          "results": [] // list of {DiscoverItem Object}s
        }
        </code></pre>
        ---
        serializer: DiscoverItemSerializer
        omit_parameters:
            - form
        parameters:
            - name: country
              paramType: query
            - name: page
              paramType: query
            - name: page_size
              paramType: query
        """
        return super(DiscoverViewSet, self).list(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        """
        Retrieve a DiscoverItem.
        ---
        serializer: DiscoverItemDetailSerializer
        """
        return super(DiscoverViewSet, self).retrieve(request, *args, **kwargs)
