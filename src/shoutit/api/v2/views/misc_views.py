# -*- coding: utf-8 -*-
"""

"""
import random
from collections import OrderedDict
from datetime import timedelta

from common.constants import POST_TYPE_OFFER, POST_TYPE_REQUEST, USER_TYPE_PAGE, USER_TYPE_PROFILE
from django.conf import settings
from django.utils import timezone
from ipware.ip import get_real_ip
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import list_route
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from shoutit.controllers import shout_controller, user_controller, location_controller
from shoutit.models import Currency, Category, PredefinedCity, CLUser, DBUser, User, DBZ2User, Shout, Tag
from shoutit.utils import debug_logger, error_logger

from . import DEFAULT_PARSER_CLASSES_v2
from ..serializers import (CategorySerializer, CurrencySerializer, ReportSerializer, PredefinedCitySerializer,
                           UserSerializer, ShoutSerializer, TagDetailSerializer)


class MiscViewSet(viewsets.ViewSet):
    """
    Other API Resources.
    """
    parser_classes = DEFAULT_PARSER_CLASSES_v2
    permission_classes = ()

    @list_route(methods=['get'], suffix='Categories')
    def categories(self, request):
        """
        List Categories
        ---
        serializer: CategorySerializer
        """
        categories = Category.objects.all().order_by('name').select_related('main_tag')
        categories_data = CategorySerializer(categories, many=True, context={'request': request}).data
        # Everyday I'm shuffling!
        shuffle = request.query_params.get('shuffle')
        if shuffle:
            random.shuffle(categories_data)
        return Response(categories_data)

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

    @list_route(methods=['get'], suffix='Suggestions')
    def suggestions(self, request):
        """
        Get suggestions for Users, Pages, Tags and Shouts. `type` query param can be passed to limit the returned fields.

        ###Request
        ```
        GET: /v2/misc/suggestions?type=users,pages,tags,shouts,shout&country=AE&state=Dubai&city=Dubai&page_size=5
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
            raise ValidationError({'error': "Invalid `page_size`"})
        type_qp = data.get('type', 'users,pages,tags,shouts,shout')
        country = data.get('country', '').upper()
        try:
            types = type_qp.split(',')
        except AttributeError:
            raise ValidationError({'error': "Invalid `type` parameter"})

        suggestions = OrderedDict()

        if 'users' in types:
            users_qs = User.objects.filter(type=USER_TYPE_PROFILE, is_activated=True).order_by('-date_joined')
            if country:
                users_qs = users_qs.filter(profile__country=country)
            users = UserSerializer(users_qs[:page_size], many=True, context={'request': request}).data
            suggestions['users'] = users
        if 'pages' in types:
            pages_qs = User.objects.filter(type=USER_TYPE_PAGE).order_by('-date_joined')
            if country:
                pages_qs = pages_qs.filter(page__country=country)
            pages = UserSerializer(pages_qs[:page_size], many=True, context={'request': request}).data
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
            "text": "the reason of this report, any text",
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
            "text": "the reason of this report, any text",
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
        raise Exception("Fake error request from ip: {}".format(get_real_ip(request) or 'undefined'))

    @list_route(methods=['get', 'post', 'delete', 'put', 'patch', 'head', 'options'], suffix='IP')
    def ip(self, request):
        """
        Retrieve ip from request
        """
        ip = get_real_ip(request) or 'undefined'
        debug_logger.debug("IP request from : {}".format(ip))
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
                msg = "CL ad already exits"
            elif source == 'dbz':
                DBUser.objects.get(db_link=link)
                msg = "DBZ ad already exits"
            elif source == 'dbz2':
                DBZ2User.objects.get(db_link=link)
                msg = "DBZ2 ad already exits"
            else:
                msg = "Unknown ad source"
            # error_logger.info(msg, extra={'link': link, 'source': source})
            return Response({'error': msg})
        except (CLUser.DoesNotExist, DBUser.DoesNotExist, DBZ2User.DoesNotExist):
            pass

        # user creation
        try:
            location = location_controller.from_location_index(shout['lat'], shout['lng'])
            mobile = shout.get('mobile')
            if source == 'cl':
                user = user_controller.sign_up_sss4(email=shout['cl_email'], location=location, dbcl_type='cl')
            elif source in ['dbz', 'dbz2']:
                user = user_controller.sign_up_sss4(None, location=location, dbcl_type=source, db_link=shout['link'],
                                                    mobile=mobile)
            else:
                raise Exception('Unknown ad source.')
        except Exception as e:
            msg = "User Creation Error"
            error_logger.info(msg, exc_info=True)
            return Response({'error': msg, 'detail': str(e)})

        # shout creation
        try:
            shout_type = POST_TYPE_OFFER if shout['type'] == 'offer' else POST_TYPE_REQUEST
            title = shout['title']
            text = shout['description']
            price = float(shout['price']) * 100
            currency = Currency.objects.get(code=shout['currency'])
            category = Category.objects.get(name=shout['category'])
            published_at = timezone.now() + timedelta(hours=random.randrange(-5, 0), minutes=random.randrange(-59, 0))
            shout_controller.create_shout(
                user=user, shout_type=shout_type, title=title, text=text, price=price, currency=currency,
                location=location, category=category, images=shout['images'], mobile=mobile, is_sss=True,
                published_at=published_at, exp_days=settings.MAX_EXPIRY_DAYS_SSS, priority=-10
            )
        except Exception as e:
            msg = "Shout Creation Error. Deleting user"
            error_logger.info(msg, exc_info=True)
            user.delete()
            return Response({'error': msg, 'detail': str(e)})

        # good bye!
        return Response({'success': True})

    @list_route(methods=['post'], suffix='Base64 to Text')
    def b64_to_text(self, request):
        """
        Convert base64 string images to text
        """
        b64 = request.data.get('b64')
        config = request.data.get('config')
        box = request.data.get('box')
        invert = request.data.get('invert', False)
        try:
            text = base64_to_text(b64, box, config, invert)
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
        invert = request.data.get('invert', False)
        try:
            texts = base64_to_texts(b64, configs, invert)
            return Response({'texts': texts})
        except Exception as e:
            return Response({'error': str(e)})


def base64_to_text(b64, box=None, config=None, invert=False):
    import pytesseract as pytesseract
    import base64
    from PIL import Image, ImageOps
    from io import BytesIO

    data = base64.b64decode(b64)
    image = Image.open(BytesIO(data))
    if box:
        w, h = image.size
        cl, cu, cr, cd = box
        box = [0 + cl, 0 + cu, w - cr, h - cd]
        image = image.crop(box)
    if invert:
        try:
            image_no_trans = Image.new("RGB", image.size, (0, 0, 0))
            image_no_trans.paste(image, image)
            inverted_image = ImageOps.invert(image_no_trans)
            image = inverted_image
        except Exception as e:
            debug_logger.warn(str(e))
            pass
    else:
        try:
            image_no_trans = Image.new("RGB", image.size, (255, 255, 255))
            image_no_trans.paste(image, image)
            image = image_no_trans
        except Exception as e:
            debug_logger.warn(str(e))
            pass
    text = pytesseract.image_to_string(image, config=config)
    return text


def base64_to_texts(b64, configs, invert=False):
    texts = []
    for conf in configs:
        box = conf.get('box')
        config = conf.get('config')
        text = base64_to_text(b64, box, config, invert)
        texts.append(text)
    return texts
