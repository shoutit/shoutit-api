from datetime import datetime
import random
import json
import uuid
import base64
import hashlib
import hmac
import re
from django.http import HttpResponse
from shoutit import settings
import mailchimp


def generate_password():
    return random_uuid_str()[24:]


def random_uuid_str():
    return str(uuid.uuid4())


def get_ip(request):
    ip = None
    if request:
        ip = request.META.get('HTTP_X_REAL_IP')
    if not ip or ip == '':
        ip = '80.227.53.34'
    return ip


def generate_confirm_token(type):
    ran = random.Random()
    return ''.join([ran.choice(type[0]) for i in range(0, type[1])])


def generate_username():
    return str(random.randint(1000000000, 1999999999))


def correct_mobile(mobile):
    mobile = remove_non_ascii(mobile)
    mobile = mobile.replace(' ', '').replace('-', '').replace('+', '')
    if len(mobile) > 8:
        mobile = '971' + mobile[-9:]
    if len(mobile) == 12:
        return mobile
    else:
        return None


def remove_non_ascii(s):
    return "".join(i for i in s if ord(i) < 128)


def set_cookie(response, key, value, days_expire=7):
    if days_expire is None:
        max_age = 365 * 24 * 60 * 60  # one year
    else:
        max_age = days_expire * 24 * 60 * 60
    expires = datetime.datetime.strftime(datetime.datetime.utcnow() + datetime.timedelta(seconds=max_age), "%a, %d-%b-%Y %H:%M:%S GMT")
    response.set_cookie(key, value, max_age=max_age, expires=expires, domain=settings.SESSION_COOKIE_DOMAIN,
                        secure=settings.SESSION_COOKIE_SECURE or None)


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


def safe_string(value):
    c = re.compile('\\b' + ('%s|%s' % ('\\b', '\\b')).join(settings.PROFANITIES_LIST) + '\\b', re.IGNORECASE)
    return c.findall(value)


def get_shout_name_preview(text, n):
    if len(text) <= n:
        return text
    else:
        return text[0:n] + '...'


def to_seo_friendly(s, max_len=50):
    import re

    allowed_chars = ['-', '.']
    t = '-'.join(s.split())  # join words with dashes
    u = ''.join([c for c in t if c.isalnum() or c in allowed_chars])  # remove punctuation
    u = u[:max_len].rstrip(''.join(allowed_chars)).lower()  # clip to max_len
    u = re.sub(r'([' + r','.join(allowed_chars) + r'])\1+', r'\1', u)  # keep one occurrence of allowed chars
    return u


def full_url_path(url):
    if isinstance(url, basestring):
        if url.startswith('/'):
            return settings.SITE_LINK + url[1:]
    return url


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
