# -*- coding: utf-8 -*-
"""

"""
from __future__ import unicode_literals

import json
import re

from django.conf import settings
from ipware.ip import get_real_ip
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import list_route
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from common.constants import POST_TYPE_OFFER
from common.constants import POST_TYPE_REQUEST
from shoutit import utils
from shoutit.api.v2.renderers import PlainTextRenderer
from shoutit.api.v2.serializers import (CategorySerializer, CurrencySerializer, ReportSerializer,
                                        PredefinedCitySerializer)
from shoutit.controllers import shout_controller, user_controller, message_controller, location_controller
from shoutit.controllers.facebook_controller import (update_linked_facebook_account_scopes,
    delete_linked_facebook_account)
from shoutit.models import (Currency, Category, PredefinedCity, CLUser, DBUser, DBCLConversation, User, DBZ2User)
from shoutit.utils import debug_logger, error_logger, parse_signed_request


class MiscViewSet(viewsets.ViewSet):
    """
    Other API Resources.
    """
    permission_classes = ()

    @list_route(methods=['get'], suffix='Categories')
    def categories(self, request):
        """
        List Categories
        ---
        serializer: CategorySerializer
        """
        categories = Category.objects.all().order_by('name').select_related('main_tag')
        serializer = CategorySerializer(categories, many=True, context={'request': request})
        return Response(serializer.data)

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

    @list_route(methods=['get'], suffix='Shouts Sort Types')
    def shouts_sort_types(self, request):
        """
        List Sort types for shouts
        ---
        """
        return Response([
            {'type': 'time', 'name': 'Latest'},
            {'type': 'distance', 'name': 'Nearest'},
            {'type': 'price_asc', 'name': 'Price Increasing'},
            {'type': 'price_desc', 'name': 'Price Decreasing'},
            {'type': 'recommended', 'name': 'Recommended'},
        ])

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

        ###Report User
        <pre><code>
        {
            "text": "the reason of this report, any text.",
            "attached_object": {
                "user": {
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
        serializer = ReportSerializer(data=request.data, partial=True, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @list_route(methods=['get', 'post', 'delete', 'put', 'patch', 'head', 'options'], suffix='Fake Error')
    def error(self, request):
        """
        Create fake error
        """
        from ipware.ip import get_real_ip
        raise Exception("Fake error request from ip: " + get_real_ip(request) or 'undefined')

    @list_route(methods=['get', 'post', 'delete', 'put', 'patch', 'head', 'options'], suffix='IP')
    def ip(self, request):
        """
        Retrieve ip from request
        """
        ip = get_real_ip(request) or 'undefined'
        debug_logger.debug("IP request from : " + ip)
        return Response({'ip': ip})

    @list_route(methods=['get'])
    def geocode(self, request):
        """
        Retrieve full location attributes for `latlng` query param

        ###Example

        ```
        GET: /v2/misc/geocode?latlng=40.722100,-74.046900
        ```
        """
        try:
            latlng = request.query_params.get('latlng', '')
            lat = float(latlng.split(',')[0])
            lng = float(latlng.split(',')[1])
        except Exception:
            raise ValidationError({'latlng': ['missing or wrong latlng parameter']})
        ip = get_real_ip(request)
        location = location_controller.from_location_index(lat, lng, ip)
        return Response(location)

    @list_route(methods=['post'])
    def parse_google_geocode_response(self, request):
        """
        Retrieve full location attributes for `google_geocode_response`.
        ###PENDING DEPRECATION
        """
        google_geocode_response = request.data.get('google_geocode_response', {})
        try:
            location = location_controller.parse_google_geocode_response(google_geocode_response)
        except (IndexError, KeyError, ValueError):
            raise ValidationError({'google_geocode_response': "Malformed Google geocode response"})
        return Response(location)

    @list_route(methods=['post'], suffix='SSS4')
    def sss4(self, request):
        """
        Create sss shouts
        ###NOT TO BE USED BY API CLIENTS
        """
        shout = request.data.get('shout')
        # check of previous ad
        source = shout.get('source')
        link = shout.get('link', '')
        try:
            if source == 'cl':
                CLUser.objects.get(cl_email=shout.get('cl_email'))
                msg = "CL ad already exits."
            elif source == 'dbz':
                DBUser.objects.get(db_link=link)
                msg = "DBZ ad already exits."
            elif source == 'dbz2':
                DBZ2User.objects.get(db_link=link)
                msg = "DBZ2 ad already exits."
            else:
                msg = "Unknown ad source."
            # error_logger.info(msg, extra={'link': link, 'source': source})
            return Response({'error': msg})
        except (CLUser.DoesNotExist, DBUser.DoesNotExist, DBZ2User.DoesNotExist):
            pass

        # user creation
        try:
            if source == 'cl':
                user = user_controller.sign_up_sss4(email=shout['cl_email'], lat=shout['lat'],
                                                    lng=shout['lng'], city=shout['city'],
                                                    country=shout['country'], dbcl_type='cl',)
            elif source in ['dbz', 'dbz2']:
                user = user_controller.sign_up_sss4(None, lat=shout['lat'], lng=shout['lng'],
                                                    city=shout['city'], country=shout['country'],
                                                    dbcl_type=source, db_link=shout['link'],
                                                    mobile=shout.get('mobile'))
            else:
                raise Exception('Unknown ad source.')
        except Exception, e:
            msg = "User Creation Error."
            error_logger.info(msg, exc_info=True)
            return Response({'error': msg, 'detail': str(e)})

        # shout creation
        try:
            shout_type = POST_TYPE_OFFER if shout['type'] == 'offer' else POST_TYPE_REQUEST
            title = shout['title']
            text = shout['description']
            price = float(shout['price'])
            currency = Currency.objects.get(code=shout['currency'])
            category = Category.objects.get(name=shout['category'])
            tags = shout['tags']
            location = {
                'latitude': float(shout['lat']),
                'longitude': float(shout['lng']),
                'country': shout['country'],
                'city': shout['city']
            }
            shout_controller.create_shout(
                user=user, shout_type=shout_type,
                title=title, text=text, price=price, currency=currency, location=location,
                category=category, tags=tags, images=shout['images'],
                is_sss=True, exp_days=settings.MAX_EXPIRY_DAYS_SSS, priority=-10
            )
        except Exception, e:
            msg = "Shout Creation Error. Deleting user."
            error_logger.info(msg, exc_info=True)
            user.delete()
            return Response({'error': msg, 'detail': str(e)})

        # good bye!
        return Response({'success': True})

    @list_route(methods=['get', 'post', 'head'], suffix='Inbound Email')
    def inbound(self, request):
        """
        Accept inbounding emails
        ###NOT TO BE USED BY API CLIENTS
        """
        data = request.POST or request.GET or {}
        if request.method == 'POST':
            if not data:
                return Response({})
            mandrill_events = json.loads(data.get('mandrill_events'))
            msg = mandrill_events[0].get('msg') if mandrill_events else {}
            in_email = msg.get('email')
            if 'dbz-reply.com' in in_email:
                return handle_dbz_reply(in_email, msg, request)
            elif 'cl-reply.com' in in_email:
                return handle_cl_reply(msg, request)
            else:
                return Response({'error': "Unknown in_email"})
        else:
            return Response(data)

    @list_route(methods=['post'], suffix='Base64 to Text')
    def b64_to_text(self, request):
        """
        Convert base64 string images to text
        """
        b64 = request.data.get('b64')
        config = request.data.get('config')
        box = request.data.get('box')
        try:
            text = utils.base64_to_text(b64, box, config)
            return Response({'text': text})
        except Exception as e:
            return Response({'error': str(e)})

    @list_route(methods=['post'], suffix='Base64 to Text')
    def b64_to_texts(self, request):
        """
        Convert base64 string images to texts
        """
        b64 = request.data.get('b64')
        configs = request.data.get('configs')
        try:
            texts = utils.base64_to_texts(b64, configs)
            return Response({'texts': texts})
        except Exception as e:
            return Response({'error': str(e)})

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

    @list_route(methods=['get', 'post'], renderer_classes=(PlainTextRenderer,), suffix='Deauthorize a Facebook Installation')
    def fb_scopes_changed(self, request):
        """
        Get notified about a Facebook user changing Shoutit App scopes. This updates the LinkedFacebookAccount record with new scopes.
        ###NOT TO BE USED BY API CLIENTS
        ###POST
        Expects a POST body with entry as list of objects each which has a uid and other attributes.
        https://developers.facebook.com/docs/graph-api/webhooks/v2.5
        """
        hub_challenge = request.query_params.get('hub.challenge')
        if request.method == 'GET':
            return Response(hub_challenge)

        entries = request.data.get('entry', [])
        for entry in entries:
            facebook_user_id = entry.get('uid')
            if facebook_user_id:
                update_linked_facebook_account_scopes(facebook_user_id)
        return Response("OK")


def handle_dbz_reply(in_email, msg, request):
    from_email = msg.get('from_email')
    try:
        dbcl_conversation = DBCLConversation.objects.get(in_email=in_email)
    except DBCLConversation.DoesNotExist:
        error = {'error': "Unknown in_email."}
        error_logger.info(error['error'], exc_info=True)
        return Response(error)

    from_user = dbcl_conversation.to_user
    to_user = dbcl_conversation.from_user
    shout = dbcl_conversation.shout
    if from_user.cl_user:
        source = 'cl'
    elif from_user.db_user:
        source = 'dbz'
    else:
        source = 'dbz2'

    # extract actual message from email without quoted text
    text = msg.get('text')
    try:
        if source == 'cl':
            if dbcl_conversation.from_user.name in text:
                split = dbcl_conversation.from_user.name
            else:
                split = 'reply.craigslist.org'
        elif source == 'dbz':
            split = 'Dubizzle'
        else:
            split = 'dbz-reply'
        text = text.split(split)[0]
        lines = text.splitlines()
        if len(lines) >= 3:
            text = '\n'.join(lines[:-2])
        else:
            text = '\n'.join(lines)
        if text.strip() == "":
            text = '\n'.join(lines)
    except AttributeError:
        error = {'error': "Couldn't process the message text."}
        error_logger.info(error['error'], exc_info=True)
        return Response(error)

    message = message_controller.send_message(conversation=None, user=from_user, to_users=[from_user, to_user],
                                              about=shout, text=text, request=request)
    # invitations
    if source == 'cl':
        messages_count = message.conversation.messages_count
        if messages_count < 4:
            debug_logger.debug('Messages count: %s' % messages_count)
            debug_logger.debug('Sending invitation email to cl user: %s' % str(from_user))
            from_user.cl_user.send_invitation_email()
        else:
            debug_logger.debug('Messages count: %s' % messages_count)
            debug_logger.debug('Skipped sending invitation email to cl user: %s' % str(from_user))
    if source in ['dbz', 'dbz2']:
        email_exists = User.objects.filter(email=from_email).exists()
        if not email_exists:
            from_user.email = from_email
            from_user.save()
            if from_user.db_user:
                from_user.db_user.send_invitation_email()
            if from_user.dbz2_user:
                from_user.dbz2_user.send_invitation_email()

    return Response({'success': True, 'message_id': message.pk})


def handle_cl_reply(msg, request):
    text = msg.get('text')
    try:
        ref = re.search("\{ref:(.+)\}", text).groups()[0]
    except AttributeError:
        return Response({
            'error': "ref wasn't passed in the reply, we can't process the message any further."})
    try:
        text = '\n'.join(text.split('\n> ')[0].splitlines()[:-2])
    except AttributeError:
        return Response({'error': "we couldn't process the message text."})
    try:
        dbcl_conversation = DBCLConversation.objects.get(ref=ref)
    except DBCLConversation.DoesNotExist, e:
        print e
        return Response({'error': str(e)})

    from_user = dbcl_conversation.to_user
    to_user = dbcl_conversation.from_user
    shout = dbcl_conversation.shout
    message = message_controller.send_message(conversation=None, user=from_user, to_users=[from_user, to_user],
                                              about=shout, text=text, request=request)

    return Response({'success': True, 'message_id': message.pk})
