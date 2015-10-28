# -*- coding: utf-8 -*-
"""

"""
from __future__ import unicode_literals

from rest_framework import permissions, viewsets, mixins
from rest_framework.decorators import detail_route
from rest_framework_extensions.mixins import DetailSerializerMixin

from shoutit.api.v2.filters import DiscoverItemFilter, ShoutIndexFilterBackend
from shoutit.api.v2.pagination import ShoutitPageNumberPagination, PageNumberIndexPagination
from shoutit.api.v2.serializers import *  # NOQA
from shoutit.models import ShoutIndex, DiscoverItem


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
            return DiscoverItem.objects.filter(parent=None)
        else:
            return DiscoverItem.objects.all()

    def list(self, request, *args, **kwargs):
        """
        Get Discover Items based on `country` query param.

        ###Response
        <pre><code>
        {
          "count": 4, // number of results
          "next": null, // next results page url
          "previous": null, // previous results page url
          "results": [] // list of {Discover Object}
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

    @detail_route(methods=['get'], suffix='Shouts')
    def shouts(self, request, *args, **kwargs):
        """
        Get discover shouts

        [Shouts Pagination](https://docs.google.com/document/d/1Zp9Ks3OwBQbgaDRqaULfMDHB-eg9as6_wHyvrAWa8u0/edit#heading=h.97r3lxfv95pj)
        ---
        serializer: ShoutSerializer
        omit_parameters:
            - form
        parameters:
            - name: page
              paramType: query
            - name: page_size
              paramType: query
        """
        filter_backend = ShoutIndexFilterBackend()
        discover_item = self.get_object()
        extra_query_params = discover_item.shouts_query
        index_queryset = ShoutIndex.search()
        index_queryset = filter_backend.filter_queryset(request=request, index_queryset=index_queryset, view=self,
                                                        extra_query_params=extra_query_params)
        setattr(self, 'model', Shout)
        setattr(self, 'filters', {'is_disabled': False})
        setattr(self, 'select_related', ('item', 'category__main_tag', 'item__currency', 'user__profile'))
        setattr(self, 'prefetch_related', ('item__videos',))
        setattr(self, 'defer', ())
        paginator = PageNumberIndexPagination()
        page = paginator.paginate_queryset(index_queryset=index_queryset, request=request, view=self)
        serializer = ShoutSerializer(page, many=True, context={'request': request})
        return paginator.get_paginated_response(serializer.data)
