# -*- coding: utf-8 -*-
"""

"""
from __future__ import unicode_literals

from rest_framework import viewsets
from rest_framework.decorators import list_route, detail_route
from rest_framework.response import Response
from shoutit.api.v3.pagination import ShoutitPageNumberPagination, ReverseDateTimePagination
from shoutit_credit.serializers import (CreditTransactionSerializer, PromoteLabelSerializer, PromoteOptionSerializer,
                                        PromoteShoutSerializer)

# Todo (mo): Find better way of loading rules. This is important to be kept as is now.
from rules.profile import *  # noqa
from rules.shout import *  # noqa


class ShoutitCreditViewSet(viewsets.GenericViewSet):
    """
    Shoutit Credit API Resources.
    """
    pagination_class = ShoutitPageNumberPagination

    @list_route(methods=['get'], suffix='Retrieve Shoutit Credit Transactions')
    def transactions(self, request, *args, **kwargs):
        """
        List profile Credit Transactions
        ###Response
        <pre><code>
        {
            "id": "000f8017-4a01-4f39-aa82-28f8eb807dce",
            "created_at": 1463255281,
            "display": {
                "text": "You earned 1 credit for sharing Used iPhone 6s on Facebook.",
                "ranges": [
                    {
                        "length": 14,
                        "offset": 32
                    }
                ]
            },
            "app_url": "shoutit://profile?username=mo",
            "web_url": "http://www.shoutit.com/user/mo",
            "type": "in",
        }
        </code></pre>

        - `type` can be `in` or `out`

        """
        self.pagination_class = ReverseDateTimePagination
        self.serializer_class = CreditTransactionSerializer
        queryset = request.user.credit_transactions.all()
        page = self.paginate_queryset(queryset)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)


class PromoteShoutMixin(object):
    @list_route(methods=['get'], suffix='Retrieve Promote Shout Labels')
    def promote_labels(self, request, *args, **kwargs):
        """
        Retrieve Promote Shout Labels
        ###Response
        <pre><code>
        {
            "name": "PREMIUM",
            "description": "Your shout will be highlighted in all searches.",
            "color": "#FFFFD700",
            "bg_color": "#26FFD700"
        }
        </code></pre>

        - `color` and `bg_color` are in this format `#AARRGGBB`
        ---
        omit_serializer: true
        """
        self.serializer_class = PromoteLabelSerializer
        queryset = PromoteLabel.objects.all().order_by('rank')
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @list_route(methods=['get'], suffix='Retrieve Promote Shout Options')
    def promote_options(self, request, *args, **kwargs):
        """
        ###Response
        <pre><code>
        {
            "id": "7395484f-c816-43a4-a290-f6af916706a9",
            "name": "TOP RESULTS",
            "description": "Your shout will appear on top of search results.",
            "label": {
                "name": "TOP",
                "description": "Your shout will appear on top of search results.",
                "color": "#FFC0C0C0",
                "bg_color": "#26C0C0C0"
            },
            "credits": 3,
            "days": 3
        }
        </code></pre>

        - `days` can be `null`
        ---
        omit_serializer: true
        """
        self.serializer_class = PromoteOptionSerializer
        queryset = PromoteShouts.objects.all()
        queryset = sorted(queryset, key=lambda pl: pl.rank)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @detail_route(methods=['patch'], suffix='Promote Shout')
    def promote(self, request, *args, **kwargs):
        """
        Promote a Shout using a PromoteOption

        ###Body
        <pre><code>
        {
            "option": {
                "id": "7395484f-c816-43a4-a290-f6af916706a9"
            }
        }
        </code></pre>

        ###Response
        <pre><code>
        {
            "promotion": {
                "id": "06d3d8b5-57d8-445a-b1c9-a3374397fa00",
                "label": {
                    "name": "TOP PREMIUM",
                    "description": "Your shout will be highlighted and appear on top of all searches.",
                    "color": "#FFFFD700",
                    "bg_color": "#26FFD700"
                },
                "days": 5,
                "expires_at": 1466001251
            },
            "success": "The shout was successfully promoted"
        }
        </code></pre>
        ---
        omit_serializer: true
        """
        self.serializer_detail_class = PromoteShoutSerializer
        shout = self.get_object()
        serializer = self.get_serializer(instance=shout, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
