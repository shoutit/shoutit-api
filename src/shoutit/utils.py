from __future__ import unicode_literals
import random
import json
import uuid
import base64
import hashlib
import hmac
import boto
from django.core.mail import get_connection
from django.http import HttpResponse
from django_rq import job
import phonenumbers
import requests
from shoutit import settings
import mailchimp
from mixpanel import Mixpanel
from twilio.rest import TwilioRestClient
import logging
from common.IP2Location import IP2Location


# Shoutit loggers
error_logger = logging.getLogger('shoutit.error')
debug_logger = logging.getLogger('shoutit.debug')
sss_logger = logging.getLogger('shoutit.sss')

# Shoutit mixpanel
shoutit_mp = Mixpanel(settings.MIXPANEL_TOKEN)

# IP2Location instant
ip2location = IP2Location(filename=settings.IP2LOCATION_DB_BIN)

# Shoutit twilio
shoutit_twilio = TwilioRestClient(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)


def generate_password():
    return random_uuid_str()[24:]


def random_uuid_str():
    return str(uuid.uuid4())


def generate_username():
    return str(random.randint(10000000000, 19999999999))


def base64_url_decode(inp):
    inp = inp.replace('-', '+').replace('_', '/')
    padding_factor = (4 - len(inp) % 4) % 4
    inp += "=" * padding_factor
    return base64.decodestring(inp)


def parse_signed_request(signed_request='a.a', secret=settings.FACEBOOK_APP_SECRET):
    l = signed_request.split('.', 2)
    encoded_sig = l[0]
    payload = l[1]

    sig = base64_url_decode(encoded_sig)
    data = json.loads(base64_url_decode(payload))

    if data.get('algorithm').upper() != 'HMAC-SHA256':
        return None
    else:
        expected_sig = hmac.new(secret, msg=payload, digestmod=hashlib.sha256).digest()

    if sig != expected_sig:
        return None
    else:
        return data


class JsonResponse(HttpResponse):
    """
    An HTTP response class that consumes data to be serialized to JSON.
    """
    status_code = 200

    def __init__(self, data, **kwargs):
        kwargs.setdefault('content_type', 'application/json')
        data = json.dumps(data)
        super(JsonResponse, self).__init__(content=data, **kwargs)


class JsonResponseBadRequest(JsonResponse):
    status_code = 400


def get_mailchimp_api():
    return mailchimp.Mailchimp(settings.MAILCHIMP_API_KEY)


def get_google_smtp_connection():
    return get_connection(**settings.EMAIL_BACKENDS['google'])


def set_profile_image(profile, image_url=None, image_data=None):
    return _set_profile_image.delay(profile, image_url, image_data)


@job(settings.RQ_QUEUE)
def _set_profile_image(profile, image_url=None, image_data=None):
    assert image_url or image_data, 'Must pass image_url or image_data'
    # todo: better exception handling
    try:
        if not image_data:
            response = requests.get(image_url, timeout=10)
            image_data = response.content

        s3 = boto.connect_s3(settings.AWS_ACCESS_KEY_ID, settings.AWS_SECRET_ACCESS_KEY)
        bucket = s3.get_bucket('shoutit-user-image-original')
        filename = profile.user.pk + '.jpg'
        key = bucket.new_key(filename)
        key.set_metadata('Content-Type', 'image/jpg')
        key.set_contents_from_string(image_data)
        s3_image_url = 'https://user-image.static.shoutit.com/%s' % filename

        profile.image = s3_image_url
        profile.save()

    except Exception, e:
        error_logger.warn(str(e))


def alias(alias_id, original):
    if settings.DEBUG and not settings.FORCE_MP_TRACKING:
        return
    return _alias.delay(alias_id, original)


@job(settings.RQ_QUEUE)
def _alias(alias_id, original):
    shoutit_mp.alias(alias_id, original)
    debug_logger.debug("MP aliased, alias_id: %s original: %s" % (alias_id, original))


def track(distinct_id, event_name, properties=None):
    if settings.DEBUG and not settings.FORCE_MP_TRACKING:
        return
    return _track.delay(distinct_id, event_name, properties)


@job(settings.RQ_QUEUE)
def _track(distinct_id, event_name, properties=None):
    properties = properties or {}
    try:
        shoutit_mp.track(distinct_id, event_name, properties)
        debug_logger.debug("MP tracked, distinct_id: %s event_name: %s" % (distinct_id, event_name))
    except Exception as e:
        error_logger.warn("shoutit_mp.track failed", extra={'reason': str(e)})


# Location functions

def location_from_ip(ip, use_google_geocode=False):
    result = ip2location.get_all(ip)
    if use_google_geocode:
        return location_from_latlng('%s,%s' % (result.latitude or 0, result.longitude or 0))
    location = {
        'latitude': round(result.latitude or 0, 6),
        'longitude': round(result.longitude or 0, 6),
        'country': result.country_short if result.country_short != '-' else '',
        'postal_code': result.zipcode if result.zipcode != '-' else '',
        'state': result.region if result.region != '-' else '',
        'city': result.city if result.city != '-' else '',
        'address': ''
    }
    return location


def location_from_latlng(latlng):
    params = {
        'latlng': latlng,
        'language': "en"
    }
    response = requests.get("https://maps.googleapis.com/maps/api/geocode/json", params).json()
    if response.get('status', 'ZERO_RESULTS') == 'ZERO_RESULTS':
        return {'error': "Make sure you have a valid latlng param"}
    try:
        return location_from_google_geocode_response(response)
    except (IndexError, KeyError, ValueError):
        return {'error': "Malformed Google geocode response"}


def location_from_google_geocode_response(response):
    locality = ''
    postal_town = ''
    administrative_area_level_2 = ''
    administrative_area_level_1 = ''
    country = ''
    postal_code = ''

    results = response['results']
    first_result = results[0]
    address = first_result['formatted_address']
    for result in results:
        for component in result['address_components']:
            if 'locality' in component['types']:
                locality = component['long_name']

            elif 'postal_town' in component['types']:
                postal_town = component['long_name']

            elif 'administrative_area_level_2' in component['types']:
                administrative_area_level_2 = component['long_name']

            elif 'administrative_area_level_1' in component['types']:
                administrative_area_level_1 = component['long_name']

            elif 'country' in component['types']:
                country = component['short_name']

            elif 'postal_code' in component['types']:
                postal_code = component['long_name']

    location = {
        'latitude': round(float(first_result['geometry']['location']['lat']), 6),
        'longitude': round(float(first_result['geometry']['location']['lng']), 6),
        'country': country,
        'postal_code': postal_code,
        'state': administrative_area_level_1,
        'city': locality or postal_town or administrative_area_level_2 or administrative_area_level_1,
        'address': address
    }
    return location


def correct_mobile(mobile, country):
    try:
        country = country.upper()
        if country in ['KW', 'OM', 'BH', 'QA'] and not mobile.startswith('00') and mobile.startswith('0'):
            mobile = mobile[1:]
        p = phonenumbers.parse(mobile, country)
        if phonenumbers.is_valid_number(p) and phonenumbers.number_type(p) != phonenumbers.phonenumberutil.PhoneNumberType.FIXED_LINE:
            mobile = phonenumbers.format_number(p, phonenumbers.PhoneNumberFormat.E164)
        else:
            raise ValueError()
    except (phonenumbers.NumberParseException, ValueError):
        mobile = ''
    return mobile
