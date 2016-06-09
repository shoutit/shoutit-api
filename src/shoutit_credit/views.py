# -*- coding: utf-8 -*-
"""

"""
from __future__ import unicode_literals

from rest_framework import viewsets
from rest_framework.decorators import list_route, detail_route
from rest_framework.response import Response
from shoutit.api.v3.pagination import ShoutitPageNumberPagination, ReverseDateTimePagination
from shoutit_credit.serializers import CreditTransactionSerializer, PromoteLabelSerializer, PromoteOptionSerializer

# Todo (mo): Find better way of loading rules. This is important to be kept as is now.
from rules.profile import *
from rules.shout import *


class ShoutitCreditViewSet(viewsets.GenericViewSet):
    """
    Shoutit Credit API Resources.
    """
    pagination_class = ShoutitPageNumberPagination

    @list_route(methods=['get'], suffix='Retrieve Shoutit Credit Transactions')
    def transactions(self, request):
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
    def promote_labels(self, request):
        """
        Retrieve Promote Shout Labels
        ###Response
        <pre><code>
        {
            'name': "PREMIUM",
            'description': "Your shout will be highlighted in all searches.",
            'color': "#FFFFD700",
            'bg_color': "#26FFD700"
        }
        </code></pre>

        - `color` and `bg_color` are in this format `#AARRGGBB`
        ---
        omit_serializer: true
        """
        queryset = PromoteLabel.objects.all().order_by('rank')
        serializer = PromoteLabelSerializer(queryset, many=True)
        return Response(serializer.data)

    @list_route(methods=['get'], suffix='Retrieve Promote Shout Options')
    def promote_options(self, request):
        """
        ###Response
        <pre><code>
        {
            'id': "7395484f-c816-43a4-a290-f6af916706a9",
            'name': "TOP RESULTS",
            'description': "Your shout will appear on top of search results.",
            'label': {
                'name': "TOP",
                'description': "Your shout will appear on top of search results.",
                'color': "#FFC0C0C0",
                'bg_color': "#26C0C0C0"
            },
            'credits': 3,
            'days': 3
        }
        </code></pre>

        - `days` can be `null`
        ---
        omit_serializer: true
        """
        queryset = PromoteShouts.objects.all()
        queryset = sorted(queryset, key=lambda pl: pl.rank)
        serializer = PromoteOptionSerializer(queryset, many=True)
        return Response(serializer.data)

    @detail_route(methods=['post'], suffix='Promote Shout')
    def promote(self, request):
        """
        ---
        omit_serializer: true
        """
        res = {}
        return Response(res)
