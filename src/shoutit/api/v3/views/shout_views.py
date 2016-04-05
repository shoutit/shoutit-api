# -*- coding: utf-8 -*-
"""

"""
from __future__ import unicode_literals

import random

from django.views.decorators.cache import cache_control
from pydash import strings
from rest_framework import permissions, status, mixins, viewsets
from rest_framework.decorators import detail_route, list_route
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework_extensions.mixins import DetailSerializerMixin

from shoutit.api.permissions import IsOwnerModify
from shoutit.api.v3.exceptions import ShoutitBadRequest, InvalidParameter, RequiredParameter
from shoutit.controllers import shout_controller
from shoutit.models import Shout, Category, Tag
from shoutit.models.post import ShoutIndex
from shoutit.utils import has_unicode
from ..filters import ShoutIndexFilterBackend
from ..pagination import PageNumberIndexPagination
from ..serializers import ShoutSerializer, ShoutDetailSerializer, MessageSerializer, CategoryDetailSerializer
from ..views.viewsets import UUIDViewSetMixin


class ShoutViewSet(DetailSerializerMixin, UUIDViewSetMixin, mixins.ListModelMixin, mixins.RetrieveModelMixin,
                   mixins.CreateModelMixin, mixins.DestroyModelMixin, viewsets.GenericViewSet):
    """
    Shout API Resource
    """
    serializer_class = ShoutSerializer
    serializer_detail_class = ShoutDetailSerializer
    filter_backends = (ShoutIndexFilterBackend,)
    model = Shout
    filters = {'is_disabled': False}
    select_related = ('item', 'category__main_tag', 'item__currency', 'user__profile')
    prefetch_related = ('item__videos',)
    defer = ()
    pagination_class = PageNumberIndexPagination
    permission_classes = (permissions.IsAuthenticatedOrReadOnly, IsOwnerModify)

    def get_queryset(self):
        return (Shout.objects.get_valid_shouts(get_expired=True).all()
                .select_related(*self.select_related)
                .prefetch_related(*self.prefetch_related)
                .defer(*self.defer))

    def filter_queryset(self, queryset, *args, **kwargs):
        """
        Given a queryset, filter it with whichever filter backend is in use.

        You are unlikely to want to override this method, although you may need
        to call it either from a list view, or from a custom `get_object`
        method if you want to apply the configured filtering backend to the
        default queryset.
        """
        for backend in list(self.filter_backends):
            queryset = backend().filter_queryset(self.request, queryset, self, *args, **kwargs)
        return queryset

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
            - name: user
              description: user username to list his shouts
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
        result.data['related_searches'] = ['HP', 'Laptops', 'Lenovo', 'Macbook Pro']
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
        search = request.query_params.get('search', '')
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
        <pre><code>
        {
            "id": "cd2ae206-3a3d-4758-85b6-fe95612aeda0",
            "api_url": "https://api.shoutit.com/v3/shouts/cd2ae206-3a3d-4758-85b6-fe95612aeda0",
            "web_url": "https://www.shoutit.com/shout/cd2ae206-3a3d-4758-85b6-fe95612aeda0",
            "type": "offer",
            "category": {
                "name": "Cars & Motors",
                "slug": "cars-motors",
                "icon": "https://tag-image.static.shoutit.com/categories/cars-i.png",
                "image": "https://tag-image.static.shoutit.com/bb4f3137-48f2-4c86-89b8-0635ed6d426e-cars-motors.jpg"
            },
            "title": "Chevrolet Cruze 2011 Perfect Condition low mileage 59000 KM",
            "location": {
                "latitude": 25.2321179865413,
                "longitude": 51.4795259383137,
                "country": "QA",
                "postal_code": "",
                "state": "",
                "city": "Ain Khaled",
                "address": ""
            },
            "text": "Chevrolet Cruze 2011 \nPerfect Condition\nVery Low Mileage 59000 KM\nEngine is 1.8 CC\nInterior is like New \nSecond Owner\nESTMARA UP to 8/2017\nPRICE IS 25500\nشفرولية كروز موديل 2011\nبحالة ممتازة جدا جدا\nقاطع 59000 كيلومتر فقط\nنظيفة جدا من الداخل ومن الخارج\nاستمارة حتي شهر8 2017 \nالسعر 25500",
            "price": 24500.0,
            "currency": "QAR",
            "available_count": 1,
            "is_sold": false,
            "thumbnail": "https://shout-image.static.shoutit.com/d7fad80a-440d-4c9e-b9b5-d4d6264516d1-1456441369.jpg",
            "video_url": null,
            "profile": {
                "id": "6590865d-b395-4cea-8382-68fbc5f048ce",
                "type": "Profile",
                "api_url": "https://api.shoutit.com/v3/profiles/15214428592",
                "web_url": "https://www.shoutit.com/user/15214428592",
                "username": "15214428592",
                "name": "user 15214428592",
                "first_name": "user",
                "last_name": "15214428592",
                "is_activated": false,
                "image": "https://user-image.static.shoutit.com/default_male.jpg",
                "cover": "",
                "is_listening": false,
                "listeners_count": 0
            },
            "date_published": 1456431892,
            "filters": [
                {
                    "name": "Color",
                    "slug": "color",
                    "value": {
                        "name": "White",
                        "slug": "white"
                    }
                },
                {
                    "name": "Model",
                    "slug": "model",
                    "value": {
                        "name": "2016",
                        "slug": "2016"
                    }
                }
            ],
            "images": [
                "https://shout-image.static.shoutit.com/d7fad80a-440d-4c9e-b9b5-d4d6264516d1-1456441369.jpg",
                "https://shout-image.static.shoutit.com/fac19243-2680-4971-ab52-d90b2f525c19-1456441369.jpg",
                "https://shout-image.static.shoutit.com/bc40f2ca-fc5b-4fe0-8d13-1a0865f4b38b-1456441370.jpg"
            ],
            "videos": [],
            "published_on": {},
            "reply_url": "https://api.shoutit.com/v3/shouts/cd2ae206-3a3d-4758-85b6-fe95612aeda0/reply",
            "conversations": [],
            "mobile_hint": "01701...",
            "is_mobile_set": true
        }
        </code></pre>

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
        # Todo: check resolution here https://github.com/elastic/elasticsearch-dsl-py/issues/348
        extra_query_params = {
            'search': "%s %s" % (shout.item.name if not has_unicode(shout.item.name) else "", " ".join(shout.tags)),
            'country': shout.country,
            'shout_type': shout.get_type_display(),
            'category': shout.category.slug,
            'exclude_ids': [shout.pk]
        }
        shouts = self.filter_queryset(self.get_index_search(), extra_query_params=extra_query_params)
        page = self.paginate_queryset(shouts)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)

    @detail_route(methods=['get'], suffix='Call')
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
        shout = self.get_object()
        return Response({'mobile': shout.mobile if shout.is_mobile_set else None})
