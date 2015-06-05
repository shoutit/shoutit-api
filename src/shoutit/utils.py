from __future__ import unicode_literals
import random
import json
import uuid
import base64
import hashlib
import hmac
from django.core.mail import get_connection
from django.http import HttpResponse
from shoutit import settings
import mailchimp
from mixpanel import Mixpanel


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