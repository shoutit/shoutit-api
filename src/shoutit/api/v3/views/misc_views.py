# -*- coding: utf-8 -*-
"""

"""
from __future__ import unicode_literals

import random
from collections import OrderedDict
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.cache import cache_control
from ipware.ip import get_real_ip
from pydash import arrays
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import list_route
from rest_framework.parsers import FormParser
from rest_framework.response import Response
from rest_framework_extensions.cache.decorators import cache_response

from common.constants import USER_TYPE_PAGE, USER_TYPE_PROFILE
from shoutit.api.renderers import PlainTextRenderer
from shoutit.api.v3.exceptions import InvalidParameter, RequiredParameter
from shoutit.controllers import location_controller, facebook_controller
from shoutit.models import Currency, Category, PredefinedCity, User, Shout, Tag
from shoutit.settings import CACHE_CONTROL_MAX_AGE
from shoutit.utils import debug_logger
from ..serializers import (CurrencySerializer, ReportSerializer, PredefinedCitySerializer, ProfileSerializer,
                           ShoutSerializer, TagDetailSerializer, PushTestSerializer)


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

    @cache_control(max_age=CACHE_CONTROL_MAX_AGE)
    @cache_response()
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

    @cache_control(max_age=CACHE_CONTROL_MAX_AGE)
    @cache_response()
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
            raise InvalidParameter('type', _("Invalid `type`"))

        suggestions = OrderedDict()

        if 'users' in types:
            users_qs = User.objects.filter(type=USER_TYPE_PROFILE, is_activated=True).order_by('-date_joined')
            if request.user.is_authenticated():
                users_qs = users_qs.exclude(id=request.user.id)
            if country:
                users_qs = users_qs.filter(profile__country=country)
            users_qs = users_qs.select_related('profile')
            users = ProfileSerializer(users_qs[:page_size], many=True, context={'request': request}).data
            suggestions['users'] = users
        if 'pages' in types:
            pages_qs = User.objects.filter(type=USER_TYPE_PAGE).order_by('-date_joined')
            if request.user.is_authenticated():
                pages_qs = pages_qs.exclude(id=request.user.id)
            if country:
                pages_qs = pages_qs.filter(page__country=country)
            pages_qs = pages_qs.select_related('page')
            pages = ProfileSerializer(pages_qs[:page_size], many=True, context={'request': request}).data
            suggestions['pages'] = pages
        if 'tags' in types:
            tag_slugs = list(Category.objects.values_list('slug', flat=True))
            random.shuffle(tag_slugs)
            tags_qs = Tag.objects.filter(slug__in=tag_slugs[:page_size])
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
            "text": "the reason of this report, any text",
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
            "text": "the reason of this report, any text",
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
            "text": "the reason of this report, any text",
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
            "apns": "APNS_KEY",
            "gcm": "GCM_KEY",
            "payload": {
                "event_name": "new_notification",
                "title": "Deep Link",
                "body": "Check Chats!",
                "icon": "https://user-image.static.shoutit.com/477ed080-0a53-4a15-9d02-1795d2e8b875.jpg",
                "aps": {
                    "alert": {
                        "title": "Deep Link",
                        "body": "Check Chats!"
                    },
                    "badge": 0,
                    "sound": "default",
                    "category": "",
                    "expiration": null,
                    "priority": 10
                },
                "data": {
                    "app_url": "shoutit://chats"
                },
                "pushed_for": ""
            }
        }
        </code></pre>

        - `apns` is the APNS Push Token to be used for Push test
        - `gcm` is the GCM RegistrationID to be used for Push test
        - `payload` is required and will be sent as
            - custom payload properties for iOS push
            - intent extras Bundle for Android that can be retrieved via intent.getExtras()
        - `payload.aps` is iOS specific. It will not be sent to Android and can only have the listed properties
        - `payload.aps.alert` can be either a string or dict that may contain title, body, action-loc-key, loc-key or loc-args

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
            raise InvalidParameter('latlng', _('Invalid `latlng`'))
        ip = get_real_ip(request)
        location = location_controller.from_location_index(lat, lng, ip)
        return Response(location)

    @list_route(methods=['get', 'post'], authentication_classes=(), parser_classes=[FormParser],
                renderer_classes=[PlainTextRenderer], suffix='Deauthorize a Facebook App Installation')
    def fb_deauth(self, request):
        """
        Deauthorize a Facebook App Installation. This removes the LinkedFacebookAccount record from Shoutit Database.
        ###NOT TO BE USED BY API CLIENTS
        ###POST
        Expects a POST body with signed_request to be parsed against Shoutit Facebook Application secret.
        """
        signed_request = request.data.get('signed_request')
        if signed_request:
            parsed_signed_request = facebook_controller.parse_signed_request(signed_request)
            facebook_user_id = parsed_signed_request.get('user_id')
            if facebook_user_id:
                facebook_controller.delete_linked_facebook_account(facebook_user_id)
        return Response('OK')

    @list_route(methods=['get', 'post'], authentication_classes=(), renderer_classes=[PlainTextRenderer],
                suffix='Change the permission scopes of a LinkedFacebookAccount')
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
        facebook_ids = filter(None, arrays.unique(map(lambda e: e['id'], entries)))
        for facebook_id in facebook_ids:
            facebook_controller.update_linked_facebook_account_scopes(facebook_id)
        return Response('OK')
