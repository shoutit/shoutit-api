"""
Utils that are independent of Apps and their models
"""
from __future__ import unicode_literals
import sys
import re
from datetime import datetime
from django.core.exceptions import ValidationError
from django.utils.deconstruct import deconstructible
import requests
import uuid
from common.constants import NOT_ALLOWED_USERNAMES


def get_address_port(using_gunicorn=False):
    if using_gunicorn:
        from shoutit.settings_gunicorn import bind
        return bind.split(':')

    if len(sys.argv) > 1 and sys.argv[1] == "runserver":
        address_port = sys.argv[-1] if len(sys.argv) > 2 else "127.0.0.1:8000"
        if address_port.startswith("-"):
            return
        else:
            try:
                address, port = address_port.split(':')
            except ValueError:
                address, port = '', address_port
        if not address:
            address = '127.0.0.1'
        return address, port

    else:
        return '127.0.0.1', '8000'


def check_offline_mood():
    try:
        # requests.head('http://www.yourapihere.com', timeout=5)
        return False
    except requests.RequestException:
        return True


def process_tag(name):
    if not isinstance(name, basestring):
        return None
    name = name.lower()[:30]
    name = re.sub('[+&/\s]', '-', name)
    name = re.sub('[^a-z0-9-]', '', name)
    name = re.sub('([-]){2,}', '-', name)
    name = name[1:] if name.startswith('-') else name
    name = name[0:-1] if name.endswith('-') else name
    if len(name) < 2:
        return None
    return name


def process_tags(names):
    processed_tags = []
    for name in names:
        processed_tag = process_tag(name)
        if processed_tag:
            processed_tags.append(processed_tag)
    return processed_tags


def date_unix(date):
    return int((date - datetime(1970, 1, 1)).total_seconds())


@deconstructible
class AllowedUsernamesValidator(object):
    message = "'%s' can not be used as username, please choose something else."
    code = 'invalid'

    def __call__(self, value):
        if value in NOT_ALLOWED_USERNAMES:
            raise ValidationError(self.message % value, code=self.code)

    def __eq__(self, other):
        return True

validate_allowed_usernames = AllowedUsernamesValidator()


@deconstructible
class UUIDValidator(object):
    message = "'%s' is not a valid id."
    code = 'invalid'

    def __call__(self, value):
        UUIDValidator.validate(value)

    def __eq__(self, other):
        return True

    @staticmethod
    def validate(value):
        try:
            uuid.UUID(value)
        except:
            raise ValidationError(UUIDValidator.message % value, code=UUIDValidator.code)


def location_from_latlng(latlng):
    params = {
        'latlng': latlng,
        'language': "en"
    }
    response = requests.get("https://maps.googleapis.com/maps/api/geocode/json", params).json()
    if response.get('status', 'ZERO_RESULTS') == 'ZERO_RESULTS':
        return {'error': "Make sure you have a valid latlng param."}
    return location_from_google_geocode_response(response)


def location_from_google_geocode_response(response):
    locality = None
    postal_town = None
    administrative_area_level_2 = None
    administrative_area_level_1 = None
    country = None
    postal_code = None

    result = response['results'][0]
    address = result['formatted_address']
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
        'country': country,
        'postal_code': postal_code,
        'state': administrative_area_level_1,
        'city': locality or postal_town or administrative_area_level_2 or administrative_area_level_1,
        'address': address
    }
    return location