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
import nexmo as nexmo
import phonenumbers
import requests
from shoutit import settings
from shoutit.lib import mailchimp
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

# shoutit mailchimp
shoutit_mailchimp = mailchimp.Client(settings.MAILCHIMP_API_KEY)

# nexmo
nexmo_client = nexmo.Client(key=settings.NEXMO_API_KEY, secret=settings.NEXMO_API_SECRET)


def generate_password():
    return random_uuid_str()[24:]


def random_uuid_str():
    return str(uuid.uuid4())


def generate_username():
    return str(random.randint(10000000000, 19999999999))


def has_unicode(s):
    try:
        s.decode('ascii')
    except UnicodeError:
        return True
    else:
        return False


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
        error_logger.warn(str(e), exc_info=True)


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
        error_logger.warn("shoutit_mp.track failed", exc_info=True, extra={'reason': str(e)})


def subscribe_to_master_list(user):
    if settings.DEBUG:
        return
    return _subscribe_to_master_list.delay(user)


@job(settings.RQ_QUEUE_MAIL)
def _subscribe_to_master_list(user):
    try:
        location = user.location
        address = {
            'addr1': location.get('address') or 'n/a',
            'city': location.get('city') or 'n/a',
            'state': location.get('state') or location.get('city') or 'n/a',
            'zip': location.get('postal_code') or 'n/a',
            'country': location.get('country'),
        }
        merge_fields = {
            'FNAME': user.first_name,
            'LNAME': user.last_name,
            'IMAGE': user.profile.image,
        }
        if address.get('country'):
            merge_fields.update({'ADDRESS': address})
        extra_fields = {
            'location': {
                'latitude': "%s" % location.get('latitude', 0),
                'longitude': "%s" % location.get('longitude', 0)
            }
        }
        shoutit_mailchimp.add_member(list_id=settings.MAILCHIMP_MASTER_LIST_ID, email=user.email,
                                     status='subscribed', extra_fields=extra_fields, merge_fields=merge_fields)
        debug_logger.debug("Added user %s to MailChimp master list" % user)
    except mailchimp.MailChimpException as e:
        if hasattr(e.response, 'json'):
            status = e.json.get('status')
            detail = e.json.get('detail', "")
            if status == 400 and 'is already a list member' in detail:
                return
        raise


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


def send_nexmo_sms(mobile, text, len_restriction=True):
    try:
        _has_unicode = has_unicode(text)
        if len_restriction and _has_unicode and len(text) > 70:
            raise ValueError('max len 70 for unicode sms exceeded')
        if len_restriction and not _has_unicode and len(text) > 160:
            raise ValueError('max len 160 for text sms exceeded')
        message = {
            'from': 'Shoutit Adv',
            'to': mobile,
            'text': text,
            'type': 'unicode' if _has_unicode else None
        }
        res = nexmo_client.send_message(message)
        messages = res.get('messages')
        if messages and messages[0].get('status') == '9':
            raise OverflowError('Quota Exceeded')
        return True
    except Exception as e:
        debug_logger.debug(e, extra={'mobile': mobile, 'text': text, 'detail': str(e)})
        return False
