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
import requests
from shoutit import settings
import mailchimp
from mixpanel import Mixpanel
import logging

# shoutit loggers
error_logger = logging.getLogger('shoutit.error')
debug_logger = logging.getLogger('shoutit.debug')
sss_logger = logging.getLogger('shoutit.sss')

# shoutit mixpanel
shoutit_mp = Mixpanel(settings.MIXPANEL_TOKEN)


def generate_password():
    return random_uuid_str()[24:]


def random_uuid_str():
    return str(uuid.uuid4())


def generate_username():
    return str(random.randint(1000000000, 1999999999))


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


def track(distinct_id, event_name, properties=None):
    return _track.delay(distinct_id, event_name, properties)


@job(settings.RQ_QUEUE)
def _track(distinct_id, event_name, properties=None):
    properties = properties or {}
    try:
        shoutit_mp.track(distinct_id, event_name, properties)
    except Exception as e:
        error_logger.warn("shoutit_mp.track failed", extra={'reason': str(e)})
