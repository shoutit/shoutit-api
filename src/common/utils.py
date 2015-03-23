"""
Utils that are independent of Apps and their models
"""
import sys
import re
from datetime import datetime
from django.core.exceptions import ValidationError
from django.utils.deconstruct import deconstructible
import httplib2
import uuid
import math
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
    http = httplib2.Http()
    try:
        resp, content = http.request('http://www.google.com')
        return False
    except httplib2.ServerNotFoundError:
        return True


def process_tag_name(name):
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


def process_tag_names(names):
    processed_tag_names = []
    for name in names:
        processed_tag_name = process_tag_name(name)
        if processed_tag_name:
            processed_tag_names.append(processed_tag_name)
    return processed_tag_names


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


def normalized_distance(lat1, long1, lat2, long2):
    # Convert latitude and longitude to
    # spherical coordinates in radians.
    degrees_to_radians = math.pi / 180.0

    # phi = 90 - latitude
    phi1 = (90.0 - float(lat1)) * degrees_to_radians
    phi2 = (90.0 - float(lat2)) * degrees_to_radians

    # theta = longitude
    theta1 = float(long1) * degrees_to_radians
    theta2 = float(long2) * degrees_to_radians

    # Compute spherical distance from spherical coordinates.

    # For two locations in spherical coordinates
    # (1, theta, phi) and (1, theta, phi)
    # cosine( arc length ) =
    # sin phi sin phi' cos(theta-theta') + cos phi cos phi'
    # distance = rho * arc length

    cos = (math.sin(phi1) * math.sin(phi2) * math.cos(theta1 - theta2) +
           math.cos(phi1) * math.cos(phi2))
    if cos >= 1.0:
        return 0.0
    arc = math.acos(cos)

    # multiply the result by pi * radius of earth to get the actual distance(approx.)
    return arc / math.pi


def mutual_followings(streams_code1, streams_code2):
    return len(set([x for x in streams_code1.split(',')]) & set([x for x in streams_code2.split(',')]))

import numpy as np


def get_farest_point(observation, points):
    observation = np.array(observation)
    points = np.array(points)

    diff = points - observation
    dist = np.sqrt(np.sum(diff ** 2, axis=-1))
    farest_index = np.argmax(dist)
    return farest_index


def safe_sql(value):
    return value.replace('\'', '\'\'')

