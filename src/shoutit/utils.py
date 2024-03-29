# -*- coding: utf-8 -*-
import logging
import random
from datetime import timedelta
from urllib import parse

import nexmo as nexmo
import phonenumbers
import rq
from django.core.exceptions import ValidationError
from django.http import HttpRequest
from django.utils.timezone import now as django_now
from django.utils.translation import ugettext_lazy as _
from django_rq.queues import DjangoRQ
from raven import Client
from raven.transport import HTTPTransport
from rest_framework.request import Request
from rq.contrib.sentry import register_sentry

from common.constants import COUNTRY_ISO
from common.lib import location
from shoutit import settings
from shoutit.api.versioning import ShoutitNamespaceVersioning

# Shoutit loggers
error_logger = logging.getLogger('shoutit.error')
debug_logger = logging.getLogger('shoutit.debug')
sss_logger = logging.getLogger('shoutit.sss')

# IP2Location instant
ip2location = location.IP2Location(filename=settings.IP2LOCATION_DB_BIN)

# nexmo
nexmo_client = nexmo.Client(key=settings.NEXMO_API_KEY, secret=settings.NEXMO_API_SECRET)


class SentryAwareWorker(rq.Worker):
    queue_class = DjangoRQ

    def __init__(self, *args, **kwargs):
        super(SentryAwareWorker, self).__init__(*args, **kwargs)
        dsn = settings.RAVEN_CONFIG['dsn']
        environment = settings.RAVEN_CONFIG['environment']
        client = Client(dsn, transport=HTTPTransport, environment=environment)
        register_sentry(client, self)


def generate_username():
    return str(random.randint(10000000000, 19999999999))[1:]


def has_unicode(s):
    for c in s:
        if ord(c) >= 128:
            return True
    return False


def correct_mobile(mobile, country, raise_exception=False):
    try:
        mobile = mobile.replace(' ', '')
        country = country.upper()
        if country in ['KW', 'OM', 'BH', 'QA'] and not mobile.startswith('00') and mobile.startswith('0'):
            mobile = mobile[1:]
        p = phonenumbers.parse(mobile, country)
        fixed_line = phonenumbers.phonenumberutil.PhoneNumberType.FIXED_LINE
        if phonenumbers.is_valid_number(p) and phonenumbers.number_type(p) != fixed_line:
            mobile = phonenumbers.format_number(p, phonenumbers.PhoneNumberFormat.E164)
        else:
            raise ValueError()
    except (phonenumbers.NumberParseException, ValueError):
        if raise_exception:
            raise ValidationError(_("Is not valid in %(country)s") % {'country': COUNTRY_ISO[country]})
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


def now_plus_delta(**kwargs):
    """
    Returns an aware or naive datetime.datetime, depending on settings.USE_TZ with delta.
    """
    now = django_now()
    if kwargs:
        return now + timedelta(**kwargs)
    return now


def blank_to_none(ret, fields):
    for field in fields:
        if field in ret and ret[field] == '':
            ret[field] = None


def none_to_blank(obj, attribute):
    for attr in attribute:
        if hasattr(obj, attr) and getattr(obj, attr) is None:
            setattr(obj, attr, '')


def create_fake_request(version):
    django_request = HttpRequest()
    django_request.META['SERVER_NAME'] = 'api.shoutit.com'
    django_request.META['SERVER_PORT'] = '80'
    request = Request(django_request)
    request.version = version
    request.versioning_scheme = ShoutitNamespaceVersioning()
    request.agent = None
    request.app_version = ''
    request.build_no = 0
    request.os_version = ''
    return request


class UserIds(list):
    def __repr__(self):
        return "UserIds: %d ids" % len(self)


def url_with_querystring(url, params=None, **kwargs):
    url_parts = list(parse.urlparse(url))
    query = dict(parse.parse_qsl(url_parts[4]))
    if isinstance(params, dict):
        query.update(params)
    query.update(kwargs)
    url_parts[4] = parse.urlencode(query)
    return parse.urlunparse(url_parts)

# @receiver(post_save)
# def model_post_save(sender, instance=None, created=False, **kwargs):
#     action = 'Created' if created else 'Updated'
#     debug_logger.debug("%s %s" % (action, repr(instance).decode('utf8')))
#
#
# @receiver(post_delete)
# def model_post_delete(sender, instance=None, created=False, **kwargs):
#     debug_logger.debug("Deleted %s" % repr(instance).decode('utf8'))
