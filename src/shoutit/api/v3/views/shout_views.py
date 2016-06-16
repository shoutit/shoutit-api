# -*- coding: utf-8 -*-
"""

"""
from __future__ import unicode_literals

import random

from django.conf import settings
from django.http import Http404
from django.views.decorators.cache import cache_control
from pydash import strings
from rest_framework import permissions, status, mixins, viewsets
from rest_framework.decorators import detail_route, list_route
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework_extensions.mixins import DetailSerializerMixin

from common.utils import any_in
from shoutit.api.permissions import IsOwnerModify
from shoutit.api.v3.exceptions import ShoutitBadRequest, InvalidParameter, RequiredParameter
from shoutit.controllers import shout_controller, mixpanel_controller
from shoutit.models import Shout, Category, Tag
from shoutit.models.post import ShoutIndex
from shoutit.utils import has_unicode
from ..filters import ShoutIndexFilterBackend
from ..pagination import PageNumberIndexPagination
from ..serializers import ShoutSerializer, ShoutDetailSerializer, MessageSerializer, CategoryDetailSerializer
from ..views.viewsets import UUIDViewSetMixin
from shoutit_credit.views import PromoteShoutMixin


class ShoutViewSet(DetailSerializerMixin, UUIDViewSetMixin, mixins.ListModelMixin, mixins.RetrieveModelMixin,
                   mixins.CreateModelMixin, mixins.DestroyModelMixin, viewsets.GenericViewSet, PromoteShoutMixin):
    """
    Shout API Resource
    """
    serializer_class = ShoutSerializer
    serializer_detail_class = ShoutDetailSerializer
    filter_backends = (ShoutIndexFilterBackend,)
    model = Shout
    get_expired = False
    select_related = ('item', 'category__main_tag', 'item__currency', 'user__profile')
    prefetch_related = ('item__videos',)
    pagination_class = PageNumberIndexPagination
    permission_classes = (permissions.IsAuthenticatedOrReadOnly, IsOwnerModify)

    def get_queryset(self):
        qs = Shout.objects.get_valid_shouts(get_expired=self.get_expired).all()
        qs = qs.select_related(*self.select_related)
        qs = qs.prefetch_related(*self.prefetch_related)
        return qs

    def filter_queryset(self, queryset, *args, **kwargs):
        """
        Given a queryset, filter it with whichever filter backend is in use.
        This is modified to allow passing extra args and kwargs to the filter backend.
        """
        for backend in list(self.filter_backends):
            queryset = backend().filter_queryset(self.request, queryset, self, *args, **kwargs)
        return queryset

    def get_object(self):
        self.get_expired = True
        shout = super(ShoutViewSet, self).get_object()
        if shout.is_expired and self.request.user != shout.owner:
            raise Http404
        return shout

    def get_index_search(self):
        return ShoutIndex.search()

    def list(self, request, *args, **kwargs):
        """
        List shouts.
        [Shouts Pagination](https://github.com/shoutit/shoutit-api/wiki/Searching-Shouts#pagination)
        ###Response
        <pre><code>
        {
            "count": 59, // number of results
            "next": null, // next results page url
            "previous": null, // previous results page url
            "results": [] // list of {ShoutSerializer}
            "related_searches": [] // list of keywords related to the current search [currently dummy text is being returned]
        }
        </code></pre>
        ---
        serializer: ShoutSerializer
        parameters:
            - name: search
              description: space or comma separated keywords to search in title, text, tags
              paramType: query
            - name: shout_type
              paramType: query
              defaultValue: all
              enum:
                - request
                - offer
                - all
            - name: country
              paramType: query
            - name: city
              paramType: query
            - name: state
              paramType: query
            - name: category
              description: the category slug
              paramType: query
            - name: tags
              description: space or comma separated tags. returned shouts will contain ALL of them. passing single tag is also possible to list its shouts
              paramType: query
            - name: discover
              description: discover item id to list its shouts
              paramType: query
            - name: profile
              description: profile username to list its shouts
              paramType: query
            - name: min_price
              paramType: query
            - name: max_price
              paramType: query
            - name: down_left_lat
              description: -90 to 90, can not be greater than up_right_lat
              paramType: query
            - name: down_left_lng
              description: -180 to 180, can not be greater than up_right_lng
              paramType: query
            - name: up_right_lat
              description: -90 to 90
              paramType: query
            - name: up_right_lng
              description: -180 to 180
              paramType: query
        """
        shouts = self.filter_queryset(self.get_index_search())
        page = self.paginate_queryset(shouts)
        serializer = self.get_serializer(page, many=True)
        result = self.get_paginated_response(serializer.data)

        # Todo: add actual data
        result.data['web_url'] = settings.SITE_LINK + 'search?src=api'
        result.data['related_searches'] = []

        # Track, skip when requests shouts of a Profile, Tag or Discover
        search_data = getattr(shouts, 'search_data', {})
        if not any_in(['profile', 'tag', 'discover'], search_data.keys()):
            search_data.update({
                'num_results': result.data.get('count'),
                'api_client': getattr(request, 'api_client', None),
                'api_version': request.version,
            })
            event_name = 'search' if 'search' in search_data else 'browse'
            mixpanel_controller.track(request.user.pk, event_name, search_data)
        return result

    @cache_control(max_age=60 * 60 * 24)
    @list_route(methods=['get'], suffix='Categories')
    def categories(self, request):
        """
        List Categories

        Passing `shuffle=1` will return randomized results
        ---
        serializer: CategoryDetailSerializer
        """
        categories = Category.objects.all().order_by('name').select_related('main_tag')
        categories_data = CategoryDetailSerializer(categories, many=True, context={'request': request}).data
        # Everyday I'm shuffling!
        shuffle = request.query_params.get('shuffle')
        if shuffle:
            random.shuffle(categories_data)
        return Response(categories_data)

    @cache_control(max_age=60 * 60 * 24)
    @list_route(methods=['get'], suffix='Shouts Sort Types')
    def sort_types(self, request):
        """
        List Sort types for shouts
        ---
        """
        return Response([
            {'type': 'time', 'name': 'Latest'},
            # {'type': 'distance', 'name': 'Nearest'},
            {'type': 'price_asc', 'name': 'Price Increasing'},
            {'type': 'price_desc', 'name': 'Price Decreasing'},
            # {'type': 'recommended', 'name': 'Recommended'},
        ])

    @list_route(methods=['get'], suffix='Shouts Auto-completion')
    def autocomplete(self, request):
        """
        List autocomplete terms that can be used for search suggestions (to be improved)

        `search` is required while `category` and `country` are optional.
        ###Response
        <pre><code>
        [
          {
            "term": "bmw-z4"
          },
          {
            "term": "bmw"
          },
        ]
        </code></pre>
        ---
        omit_serializer: true
        parameters:
            - name: search
              description: At least two characters
              paramType: query
            - name: category
              description: Slug for the Category to return terms within it
              paramType: query
            - name: country
              description: Code for the Country to return terms used in it
              paramType: query
        """
        # Todo: improve!
        search = request.query_params.get('search', '').strip()
        if not search:
            raise RequiredParameter('search', "This parameter is required")
        # category = request.query_params.get('category')
        # country = request.query_params.get('country')
        if len(search) >= 2:
            terms = list(Tag.objects.filter(name__istartswith=search).values_list('name', flat=True)[:10])
            random.shuffle(terms)
            terms = map(lambda t: {'term': strings.human_case(t)}, terms)
        else:
            raise InvalidParameter('search', "At least two characters are required")
        return Response(terms)

    def create(self, request, *args, **kwargs):
        """
        Create a Shout
        ###REQUIRES AUTH
        ###Request
        ####Body Example
        <pre><code>
        {
            "type": "offer",
            "title": "BMW M6",
            "text": "Brand new black bmw m6 2016.",
            "price": 1000,
            "currency": "EUR",
            "available_count": 4,
            "is_sold": false,
            "images": [],
            "videos": [],
            "category": {
                "slug": "cars-motors"
            },
            "location": {
                "latitude": 25.1593957,
                "longitude": 55.2338326,
                "address": "Whatever Street 31"
            },
            "publish_to_facebook": true,
            "filters": [
                {
                    "slug": "color",
                    "value": {
                        "slug": "white"
                    }
                },
                {
                    "slug": "model",
                    "value": {
                        "slug": "2016"
                    }
                }
            ],
            "mobile": "01701700555"
        }
        </code></pre>

        ###Valid cases
        1. Offer with either one of the following: `title`, `images` or `videos` *
        2. Request with a `title`

        * For `images` and `videos` at least a single item is required

        ---
        serializer: ShoutDetailSerializer
        omit_parameters:
            - form
        parameters:
            - name: body
              paramType: body
        """
        serializer = ShoutDetailSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def retrieve(self, request, *args, **kwargs):
        """
        Retrieve a Shout

        [Shout object](https://github.com/shoutit/shoutit-api/wiki/Intro-to-Shouts)
        ---
        serializer: ShoutDetailSerializer
        """
        return super(ShoutViewSet, self).retrieve(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        """
        Modify a Shout
        ###REQUIRES AUTH
        ###Request
        ####Body
        Just like creating shouts, however all attributes are optional. `type` changing is not allowed and will be ignored
        </code></pre>
        ---
        serializer: ShoutDetailSerializer
        omit_parameters:
            - form
        parameters:
            - name: body
              paramType: body
        """
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        """
        Delete a Shout
        ###REQUIRES AUTH
        ---
        omit_serializer: true
        omit_parameters:
            - form
        """
        return super(ShoutViewSet, self).destroy(request, *args, **kwargs)

    def perform_destroy(self, instance):
        shout_controller.delete_post(instance)

    @detail_route(methods=['post'], suffix='Reply')
    def reply(self, request, *args, **kwargs):
        """
        Send message to the owner about this Shout
        ###REQUIRES AUTH
        ###Request
        <pre><code>
        {
            "text": "text goes here",
            "attachments": [
                {
                    "shout": {
                        "id": ""
                    }
                },
                {
                    "profile": {
                        "id": ""
                    }
                },
                {
                    "location": {
                        "latitude": 12.345,
                        "longitude": 12.345
                    }
                },
                {
                    "images": [], // list of image urls
                    "videos": [] // list of {Video Object}s
                }
            ]
        }
        </code></pre>

        Either `text`, `attachments` or both has to be provided. Images and videos are to be compressed and uploaded before submitting. CDN urls should be sent.
        ---
        serializer: MessageSerializer
        omit_parameters:
            - form
        parameters:
            - name: body
              paramType: body
        """
        shout = self.get_object()
        if request.user == shout.owner:
            raise ShoutitBadRequest("You can not start a conversation about your own shout")
        context = {
            'request': request,
            'conversation': None,
            'to_users': [shout.owner],
            'about': shout
        }
        serializer = MessageSerializer(data=request.data, partial=True, context=context)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        headers = self.get_success_message_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def get_success_message_headers(self, data):
        loc = reverse('conversation-messages', kwargs={'id': data['conversation_id']}, request=self.request)
        return {'Location': loc}

    @detail_route(methods=['get'], suffix='Related shouts')
    def related(self, request, *args, **kwargs):
        """
        List related shouts to this Shout
        ---
        serializer: ShoutSerializer
        omit_parameters:
            - form
        parameters:
            - name: shout_type
              paramType: query
              defaultValue: all
              enum:
                - request
                - offer
                - all
            - name: page
              paramType: query
            - name: page_size
              paramType: query
        """
        shout = self.get_object()
        # Shouts with long unicode titles can't be fuzzily searched
        # https://github.com/elastic/elasticsearch-dsl-py/issues/348
        if not has_unicode(shout.item.name):
            title = shout.item.name
        else:
            title = ""
        search = "%s %s" % (title, " ".join(shout.tags))
        extra_query_params = {
            'search': search,
            'country': shout.country,
            'shout_type': shout.get_type_display(),
            'category': shout.category.slug,
            'exclude': shout.pk
        }
        shouts = self.filter_queryset(self.get_index_search(), extra_query_params=extra_query_params)
        page = self.paginate_queryset(shouts)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)

    @detail_route(methods=['get'], suffix='Call', permission_classes=[permissions.IsAuthenticated])
    def call(self, request, *args, **kwargs):
        """
        Get the mobile of this Shout
        ##Response
        <pre><code>
        {
            "mobile": "01701700555"
        }
        </code></pre>

        This endpoint will be throttled to prevent multiple requests from same client in short time.
        ---
        omit_serializer: true
        omit_parameters:
            - form
        """
        user = request.user
        profile = user.ap
        shout = self.get_object()
        mobile = shout.mobile if shout.is_mobile_set else None
        if not mobile:
            raise ShoutitBadRequest(message="No mobile to be called")
        track_properties = {
            'api_client': getattr(request, 'api_client', None),
            'api_version': request.version,
            'mp_country_code': profile.country,
            '$region': profile.state,
            '$city': profile.city,
            'shout_id': shout.pk,
            'shout_country': shout.get_country_display(),
            'shout_region': shout.state,
            'shout_city': shout.city,
        }
        mixpanel_controller.track(user.pk, 'show_mobile', track_properties)
        return Response({'mobile': mobile})
