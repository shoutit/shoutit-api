# -*- coding: utf-8 -*-
"""

"""
from __future__ import unicode_literals

import random
from collections import OrderedDict

from django.views.decorators.cache import cache_control
from ipware.ip import get_real_ip
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import list_route
from rest_framework.response import Response

from common.constants import USER_TYPE_PAGE, USER_TYPE_PROFILE
from shoutit.api.renderers import PlainTextRenderer
from shoutit.api.v3.exceptions import InvalidParameter, RequiredParameter
from shoutit.controllers import location_controller
from shoutit.controllers.facebook_controller import (update_linked_facebook_account_scopes,
                                                     delete_linked_facebook_account)
from shoutit.models import (Currency, Category, PredefinedCity, User, Shout,
                            Tag)
from shoutit.utils import debug_logger, parse_signed_request
from ..serializers import (CurrencySerializer, ReportSerializer, PredefinedCitySerializer,
                           ProfileSerializer, ShoutSerializer, TagDetailSerializer, PushTestSerializer)


class MiscViewSet(viewsets.ViewSet):
    """
    Other API Resources.
    """
    permission_classes = ()

    @list_route(methods=['get'], suffix='Cities')
    def cities(self, request):
        """
        List Cities
        ---
        serializer: PredefinedCitySerializer
        """
        cities = PredefinedCity.objects.filter(approved=True)
        serializer = PredefinedCitySerializer(cities, many=True, context={'request': request})
        return Response(serializer.data)

    @cache_control(max_age=60 * 60 * 24)
    @list_route(methods=['get'], suffix='Currencies')
    def currencies(self, request):
        """
        List Currencies
        ---
        serializer: CurrencySerializer
        """
        currencies = Currency.objects.all()
        serializer = CurrencySerializer(currencies, many=True, context={'request': request})
        return Response(serializer.data)

    @list_route(methods=['get'], suffix='Suggestions')
    def suggestions(self, request):
        """
        Get suggestions for Users, Pages, Tags and Shouts. `type` query param can be passed to limit the returned fields.

        ###Request
        ```
        GET: /misc/suggestions?type=users,pages,tags,shouts,shout&country=AE&state=Dubai&city=Dubai&page_size=5
        ```

        ###Response
        <pre><code>
        {
            "users": [],
            "pages": [],
            "tags": [],
            "shouts": [],
            "shout": {}
        }
        </code></pre>

        ---
        omit_serializer: true
        omit_parameters:
            - form
        """
        data = request.query_params
        try:
            page_size = int(data.get('page_size', 5))
        except ValueError:
            raise InvalidParameter('page_size', "Invalid `page_size`")
        type_qp = data.get('type', 'users,pages,tags,shouts,shout')
        country = data.get('country', '').upper()
        try:
            types = type_qp.split(',')
        except:
            raise InvalidParameter('type', "Invalid `type`")

        suggestions = OrderedDict()

        if 'users' in types:
            users_qs = User.objects.filter(type=USER_TYPE_PROFILE, is_activated=True).order_by('-date_joined')
            if country:
                users_qs = users_qs.filter(profile__country=country)
            users = ProfileSerializer(users_qs[:page_size], many=True, context={'request': request}).data
            suggestions['users'] = users
        if 'pages' in types:
            pages_qs = User.objects.filter(type=USER_TYPE_PAGE).order_by('-date_joined')
            if country:
                pages_qs = pages_qs.filter(page__country=country)
            pages = ProfileSerializer(pages_qs[:page_size], many=True, context={'request': request}).data
            suggestions['pages'] = pages
        if 'tags' in types:
            tag_names = list(Category.objects.all().values_list("main_tag__name", flat=True))
            random.shuffle(tag_names)
            tags_qs = Tag.objects.filter(name__in=tag_names[:page_size])
            tags = TagDetailSerializer(tags_qs, many=True, context={'request': request}).data
            suggestions['tags'] = tags
        if 'shouts' in types or 'shout' in types:
            shouts_qs = Shout.objects.get_valid_shouts(country=country).order_by('-published_at')
            if 'shouts' in types:
                shouts = ShoutSerializer(shouts_qs[:page_size], many=True, context={'request': request}).data
                suggestions['shouts'] = shouts
            if 'shout' in types:
                shout = shouts_qs.first()
                if shout:
                    shout = ShoutSerializer(shout, context={'request': request}).data
                suggestions['shout'] = shout
        return Response(suggestions)

    @list_route(methods=['post'], permission_classes=(permissions.IsAuthenticatedOrReadOnly,), suffix='Reports')
    def reports(self, request):
        """
        Create Report

        ###REQUIRES AUTH
        ###Report Shout
        <pre><code>
        {
            "text": "the reason of this report, any text.",
            "attached_object": {
                "shout": {
                    "id": ""
                }
            }
        }
        </code></pre>

        ###Report Profile
        <pre><code>
        {
            "text": "the reason of this report, any text.",
            "attached_object": {
                "profile": {
                    "id": ""
                }
            }
        }
        </code></pre>

        ###Report Conversation (`public_chat`)
        <pre><code>
        {
            "text": "the reason of this report, any text.",
            "attached_object": {
                "conversation": {
                    "id": ""
                }
            }
        }
        </code></pre>
        ---
        serializer: ReportSerializer
        omit_parameters:
            - form
        parameters:
            - name: body
              paramType: body
        """
        serializer = ReportSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @list_route(methods=['post'], permission_classes=(permissions.IsAuthenticated,), suffix='Send Push Test')
    def push(self, request):
        """
        Send push test

        ###REQUIRES AUTH
        ###Report Shout
        <pre><code>
        {
            "type": "android",
            "token": "",
            "aps_data": {
                "alert": {},
                "badge": 3,
                "sound": "default",
                "category": ""
            },
            "payload": {
                "event_name": "new_notification",
                "title": "Push test",
                "body": "Hi there",
                "icon": "",
                "data": {
                    "app_url": ""
                }
            }
        }
        </code></pre>

        - `type` can be either `android` or `ios`
        - `type` and `token` are required
        - `aps_data` is iOS specific and can only have the mentioned properties
        - `alert` can either be a string or dict that may contain title, body and icon, action-loc-key, loc-key or loc-args
        - `payload` properties will be sent as
            - extra payload properties for iOS
            - properties inside a `data` dict in Android payload

        ---
        serializer: PushTestSerializer
        omit_parameters:
            - form
        parameters:
            - name: body
              paramType: body
        """
        serializer = PushTestSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({'success': True}, status=status.HTTP_201_CREATED)

    @list_route(methods=['get', 'post', 'delete', 'put', 'patch', 'head', 'options'], suffix='Fake Error')
    def error(self, request):
        """
        Create fake error
        """
        from ipware.ip import get_real_ip
        raise Exception("Fake error request from ip: " + get_real_ip(request) or 'undefined')

    @list_route(methods=['get'], suffix='Get IP')
    def ip(self, request):
        """
        Retrieve ip from request
        """
        ip = get_real_ip(request) or 'undefined'
        debug_logger.debug("IP request from : " + ip)
        return Response({'ip': ip})

    @list_route(methods=['get'], suffix='Geocode')
    def geocode(self, request):
        """
        Retrieve full location attributes for `latlng` query param

        ###Example

        ```
        GET: /misc/geocode?latlng=40.722100,-74.046900
        ```
        """
        latlng = request.query_params.get('latlng')
        if not latlng:
            raise RequiredParameter('latlng')
        try:
            lat = float(latlng.split(',')[0])
            lng = float(latlng.split(',')[1])
        except Exception:
            raise InvalidParameter('latlng', 'Invalid `latlng`')
        ip = get_real_ip(request)
        location = location_controller.from_location_index(lat, lng, ip)
        return Response(location)

    @list_route(methods=['post'], suffix='Deauthorize a Facebook Installation')
    def fb_deauth(self, request):
        """
        Deauthorize a Facebook Installation. This removes the LinkedFacebookAccount record from Shoutit Database.
        ###NOT TO BE USED BY API CLIENTS
        ###POST
        Expects a POST body with signed_request to be parsed against Shoutit Facebook Application secret.
        """
        signed_request = request.data.get('signed_request')
        if signed_request:
            parsed_signed_request = parse_signed_request(signed_request)
            facebook_user_id = parsed_signed_request.get('user_id')
            if facebook_user_id:
                delete_linked_facebook_account(facebook_user_id)
        return Response()

    @list_route(methods=['get', 'post'], renderer_classes=(PlainTextRenderer,),
                suffix='Deauthorize a Facebook Installation')
    def fb_scopes_changed(self, request):
        """
        Get notified about a Facebook user changing Shoutit App scopes. This updates the LinkedFacebookAccount record with new scopes.
        ###NOT TO BE USED BY API CLIENTS
        ###POST
        Expects a POST body with entry as list of objects each which has a uid and other attributes.
        https://developers.facebook.com/docs/graph-api/webhooks/v2.5
        """
        hub_challenge = request.query_params.get('hub.challenge', '')
        if request.method == 'GET':
            return Response(hub_challenge)

        entries = request.data.get('entry', [])
        for entry in entries:
            facebook_user_id = entry.get('uid')
            if facebook_user_id:
                update_linked_facebook_account_scopes(facebook_user_id)
        return Response("OK")
