# -*- coding: utf-8 -*-
"""

"""
from __future__ import unicode_literals
import json
import re
import logging
from django.conf import settings

from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import list_route

from shoutit.api.v2.serializers import (CategorySerializer, CurrencySerializer, ReportSerializer,
                                        PredefinedCitySerializer)
from shoutit.controllers import shout_controller, user_controller, message_controller
from shoutit.models import (Currency, Category, PredefinedCity, CLUser, DBUser, DBCLConversation,
                            User)
error_logger = logging.getLogger('shoutit.error')
logger = logging.getLogger('shoutit.debug')


class MiscViewSet(viewsets.ViewSet):
    """
    Other API Resources.
    """

    permission_classes = ()

    @list_route(methods=['get'], suffix='Currencies')
    def currencies(self, request):
        """
        Get currencies
        ---
        serializer: CurrencySerializer
        """
        currencies = Currency.objects.all()
        serializer = CurrencySerializer(currencies, many=True, context={'request': request})
        return Response(serializer.data)

    @list_route(methods=['get'], suffix='Cities')
    def cities(self, request):
        """
        Get cities
        ---
        serializer: PredefinedCitySerializer
        """
        cities = PredefinedCity.objects.filter(approved=True)
        serializer = PredefinedCitySerializer(cities, many=True, context={'request': request})
        return Response(serializer.data)

    @list_route(methods=['get'], suffix='Categories')
    def shouts_sort_types(self, request):
        """
        Get shouts sort types
        ---
        """
        return Response([
            {'type': 'time', 'name': 'Latest'},
            {'type': 'distance', 'name': 'Nearest'},
            {'type': 'price_asc', 'name': 'Price Increasing'},
            {'type': 'price_desc', 'name': 'Price Decreasing'},
            {'type': 'recommended', 'name': 'Recommended'},
        ])

    @list_route(methods=['get'], suffix='Categories')
    def categories(self, request):
        """
        Get categories
        ---
        serializer: CategorySerializer
        """
        categories = Category.objects.all()
        serializer = CategorySerializer(categories, many=True, context={'request': request})
        return Response(serializer.data)

    @list_route(methods=['post'], suffix='Reports')
    def reports(self, request):
        """
        Report

        ###Reporting Shout
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

        ###Reporting User
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

    @list_route(methods=['get', 'post', 'delete', 'put', 'patch', 'head', 'options'],
                suffix='Fake Error')
    def error(self, request):
        from ipware.ip import get_real_ip
        error_logger.error("Fake error request from ip: " + get_real_ip(request) or 'undefined')
        raise Exception("API v2 Fake Error")

    @list_route(methods=['get', 'post', 'delete', 'put', 'patch', 'head', 'options'],
                suffix='IP')
    def ip(self, request):
        from ipware.ip import get_real_ip
        ip = get_real_ip(request) or 'undefined'
        logger.debug("IP request from : " + ip)
        return Response({'ip': ip})

    @list_route(methods=['post'], suffix='SSS4')
    def sss4(self, request):
        shout = request.data.get('shout')
        # check of previous ad
        try:
            if shout['source'] == 'cl':
                CLUser.objects.get(cl_email=shout['cl_email'])
            elif shout['source'] == 'db':
                DBUser.objects.get(db_link=shout['link'])
            else:
                msg = "Unknown ad source: " + shout['source']
                error_logger.warn(msg)
                return Response({'error': msg})
            msg = "Ad already exits. " + shout['link']
            error_logger.warn(msg)
            return Response({'error': msg})
        except (CLUser.DoesNotExist, DBUser.DoesNotExist):
            pass

        # user creation
        try:
            if shout['source'] == 'cl':
                user = user_controller.sign_up_sss4(email=shout['cl_email'], lat=shout['lat'],
                                                    lng=shout['lng'],
                                                    city=shout['city'], country=shout['country'],
                                                    dbcl_type='cl')
            elif shout['source'] == 'db':
                user = user_controller.sign_up_sss4(None, lat=shout['lat'], lng=shout['lng'],
                                                    city=shout['city'],
                                                    country=shout['country'], dbcl_type='db',
                                                    db_link=shout['link'])
            else:
                raise Exception('Unknown ad source')
        except Exception, e:
            msg = "User Creation Error."
            error_logger.error(msg, extra={'detail':str(e)})
            return Response({'error': msg, 'detail': str(e)})

        # shout creation
        try:
            if shout['type'] == 'request':
                shout = shout_controller.post_request(
                    name=shout['title'], text=shout['description'], price=float(shout['price']),
                    currency=shout['currency'],
                    latitude=float(shout['lat']), longitude=float(shout['lng']),
                    country=shout['country'], city=shout['city'],
                    tags=shout['tags'], images=shout['images'], shouter=user, is_sss=True,
                    exp_days=settings.MAX_EXPIRY_DAYS_SSS, category=shout['category'], priority=-10
                )
            elif shout['type'] == 'offer':
                shout = shout_controller.post_offer(
                    name=shout['title'], text=shout['description'], price=float(shout['price']),
                    currency=shout['currency'],
                    latitude=float(shout['lat']), longitude=float(shout['lng']),
                    country=shout['country'], city=shout['city'],
                    tags=shout['tags'], images=shout['images'], shouter=user, is_sss=True,
                    exp_days=settings.MAX_EXPIRY_DAYS_SSS, category=shout['category'], priority=-10
                )

        except Exception, e:
            msg = "Shout Creation Error. Deleting user: " + str(user)
            error_logger.error(msg, extra={'detail': str(e)})
            user.delete()
            return Response({'error': msg, 'detail': str(e)})

        # good bye!
        return Response({'success': True})

    @list_route(methods=['get', 'post', 'head'], suffix='Inbound Email')
    def inbound(self, request):
        data = request.POST or request.GET or {}
        if request.method == 'GET':
            print data
            return Response(data)
        elif request.method == 'HEAD':
            return Response({})
        elif request.method == 'POST':
            if not data:
                return Response({})
            mandrill_events = json.loads(data.get('mandrill_events'))
            msg = mandrill_events[0].get('msg') if mandrill_events else {}
            in_email = msg.get('email')
            if 'dbz-reply.com' in in_email:
                return handle_db_reply(in_email, msg, request)
            elif 'cl-reply.com' in in_email:
                return handle_cl_reply(msg, request)
            else:
                return Response({'error': "Unknown in_email"})


def handle_db_reply(in_email, msg, request):
    from_email = msg.get('from_email')
    text = msg.get('text')
    try:
        dbcl_conversation = DBCLConversation.objects.get(in_email=in_email)
    except DBCLConversation.DoesNotExist:
        return Response({'error': "Unknown in_email"})
    try:
        text = '\n'.join(text.split('Dubizzle')[0].splitlines()[:-2])
    except AttributeError:
        return Response({'error': "we couldn't process the message text."})

    from_user = dbcl_conversation.to_user
    email_exists = User.objects.filter(email=from_email).exists()
    if not email_exists:
        from_user.email = from_email
        from_user.save()
    to_user = dbcl_conversation.from_user
    shout = dbcl_conversation.shout
    message = message_controller.send_message(conversation=None, user=from_user,
                                              to_users=[from_user, to_user],
                                              about=shout, text=text, request=request)
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
    message = message_controller.send_message(conversation=None, user=from_user,
                                              to_users=[from_user, to_user],
                                              about=shout, text=text, request=request)
    return Response({'success': True, 'message_id': message.pk})
