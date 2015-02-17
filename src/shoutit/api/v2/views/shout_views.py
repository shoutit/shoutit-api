# -*- coding: utf-8 -*-
"""

"""
from __future__ import unicode_literals
from math import ceil

from rest_framework import permissions, viewsets, filters, mixins, generics
from rest_framework.response import Response
from rest_framework.decorators import detail_route, list_route
from rest_framework.settings import api_settings
from common.constants import TIME_RANK_TYPE, FOLLOW_RANK_TYPE, DISTANCE_RANK_TYPE

from shoutit.controllers import shout_controller, stream_controller

from shoutit.models import Message, Trade
from shoutit.api.v2.permissions import IsContributor, IsOwnerOrReadOnly, IsOwnerOrContributorsReadOnly
from shoutit.api.renderers import render_conversation, render_message, render_shout


class ShoutViewSet(viewsets.GenericViewSet):
    """
    API endpoint that allows shouts to be listed, created, viewed updated or deleted.
    """
    lookup_field = 'id'
    lookup_value_regex = '[0-9a-f-]{32,36}'
    # serializer_class = UserSerializer2

    filter_backends = (filters.DjangoFilterBackend, filters.SearchFilter)
    filter_fields = ('id',)
    search_fields = ('id',)

    permission_classes = (permissions.IsAuthenticated, IsOwnerOrReadOnly)

    def get_queryset(self):
        return Trade.objects.all()

    def list(self, request, *args, **kwargs):
        """
        get shouts based on filters
        """
        order_by = (TIME_RANK_TYPE | FOLLOW_RANK_TYPE | DISTANCE_RANK_TYPE)

        all_shout_ids = stream_controller.get_ranked_shouts_ids(request.user, order_by)

        page_num = 1
        dict_shout_ids = dict(all_shout_ids)
        shout_ids = [k[0] for k in all_shout_ids if k in all_shout_ids[
                                                         api_settings.PAGINATE_BY * (page_num - 1): api_settings.PAGINATE_BY * page_num]]

        if len(shout_ids):
            shouts = stream_controller.get_trades_by_pks(shout_ids)
            for shout in shouts:
                shout.rank = dict_shout_ids[shout.pk]
            shouts.sort(key=lambda x: x.rank)
        else:
            shouts = []

        pages_count = int(ceil(len(all_shout_ids) / float(api_settings.PAGINATE_BY)))
        is_last_page = page_num >= pages_count
        ret = {
            "results": [render_shout(shout) for shout in shouts]
        }
        return Response(ret)

    def create(self, request, *args, **kwargs):
        """
        create shout
        """
        return Response()

    def retrieve(self, request, *args, **kwargs):
        """
        get shout
        """
        shout = self.get_object()
        return Response(render_shout(shout))

    def update(self, request, *args, **kwargs):
        """
        modify shout
        """
        shout = self.get_object()
        return Response(render_shout(shout))

    def destroy(self, request, *args, **kwargs):
        """
        delete shout
        """
        shout = self.get_object()
        return Response()

    @list_route(methods=['get'])
    def nearby(self, request, *args, **kwargs):
        """
        get nearby shouts
        """
        return Response()

    @detail_route(methods=['post'])
    def reply(self, request, *args, **kwargs):
        """
        reply to a shout
        """
        return Response()
