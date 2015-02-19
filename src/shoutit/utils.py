from datetime import datetime
import random
import json
import urlparse
import uuid
import math
import base64
import hashlib
import hmac
import StringIO
import mimetypes
import os
import re
from PIL import Image
import pyrax
import numpy as np
from django.http import HttpResponse, Http404
from django.conf import settings

from django.core.exceptions import ValidationError
from common.constants import POST_TYPE_EXPERIENCE, POST_TYPE_REQUEST, POST_TYPE_OFFER, NOT_ALLOWED_USERNAMES

from shoutit.models import Experience, Tag, User
from settings import SITE_LINK


def generate_password():
    return random_uuid_str()[24:]


def random_uuid_str():
    return str(uuid.uuid4())


def get_farest_point(observation, points):
    observation = np.array(observation)
    points = np.array(points)

    diff = points - observation
    dist = np.sqrt(np.sum(diff ** 2, axis=-1))
    farest_index = np.argmax(dist)
    return farest_index


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


https_cdn = re.compile(r'http://((?:[\w-]+\.)+)(r\d{2})\.(.*)', re.IGNORECASE)


def get_https_cdn(url):
    m = https_cdn.match(url)
    if m:
        return 'https://%sssl.%s' % (m.group(1), m.group(3))
    else:
        return url


def safe_string(value):
    c = re.compile('\\b' + ('%s|%s' % ('\\b', '\\b')).join(settings.PROFANITIES_LIST) + '\\b', re.IGNORECASE)
    return c.findall(value)


def safe_sql(value):
    return value.replace('\'', '\'\'')


def get_shout_name_preview(text, n):
    if len(text) <= n:
        return text
    else:
        return text[0:n] + '...'


def get_size_url(url, size):
    if not url:
        return url
    scheme, netloc, path, p, q, f = urlparse.urlparse(url)
    path = path.split('/')
    filename, extension = os.path.splitext(path[-1])
    filename = '%s_%d%s' % (filename, size, extension)
    path[-1] = filename
    return '%s%s%s' % (scheme and (scheme + '://') or '', netloc, '/'.join(path))


def make_image_thumbnail(url, size, container_name):
    from PIL.Image import open as image_open, ANTIALIAS
    from mimetypes import guess_type
    import StringIO
    import pyrax
    
    from django.core.files.base import ContentFile

    filename = os.path.basename(urlparse.urlparse(url)[2])
    content_type = guess_type(filename)
    name, extension = os.path.splitext(filename)

    pyrax.set_setting('identity_type', settings.CLOUD_IDENTITY)
    pyrax.set_credentials(username=settings.CLOUD_USERNAME, api_key=settings.CLOUD_API_KEY)
    cf = pyrax.cloudfiles
    container = cf.get_container(container_name)

    obj = container.get_object(filename)
    content_file = ContentFile(obj.get())
    image = image_open(content_file)
    thumb = image.copy()
    thumb.thumbnail((size, size), ANTIALIAS)
    buff = StringIO.StringIO()
    thumb.save(buff, format=image.format)
    buff.seek(0)
    new_obj = container.store_object('%s_%d%s' % (name, size, extension), data=buff.buf, content_type=content_type)


def make_cloud_thumbnails_for_image(image_url):
    make_image_thumbnail(image_url, 145, 'shout_image')
    make_image_thumbnail(image_url, 85, 'shout_image')

def make_cloud_thumbnails_for_user_image(image_url):
    make_image_thumbnail(image_url, 95, 'user_image')
    make_image_thumbnail(image_url, 32, 'user_image')


def to_seo_friendly(s, max_len=50):
    import re

    allowed_chars = ['-', '.']
    t = '-'.join(s.split())  # join words with dashes
    u = ''.join([c for c in t if c.isalnum() or c in allowed_chars])  # remove punctuation
    u = u[:max_len].rstrip(''.join(allowed_chars)).lower()  # clip to max_len
    u = re.sub(r'([' + r','.join(allowed_chars) + r'])\1+', r'\1', u)  # keep one occurrence of allowed chars
    return u


# todo: check who calls this method
def shout_link(post):
    if not post:
        return None
    post_id = post.pk

    if post.Type == POST_TYPE_EXPERIENCE:
        # todo: make sure the actual exp is passed so no need for using the model here
        if post.__class__.__name__ == 'Post':
            post = Experience.objects.get(pk=post.pk)
        experience = post
        about = to_seo_friendly(experience.AboutBusiness.name)

        city = ('-' + to_seo_friendly(unicode.lower(experience.AboutBusiness.City))) if experience.AboutBusiness.City else ''
        experience_type = 'bad' if experience.State == 0 else 'good'
        link = '%s%s-experience/%s/%s%s/' % (SITE_LINK, experience_type, post_id, about, city)
    else:
        shout = post
        shout_type = 'request' if shout.Type == POST_TYPE_REQUEST else 'offer' if shout.Type == POST_TYPE_OFFER else 'shout'
        etc = to_seo_friendly(shout.Item.Name if hasattr(shout, 'Item') else shout.trade.Item.Name)
        city = to_seo_friendly(unicode.lower(shout.ProvinceCode))
        link = '%s%s/%s/%s-%s/' % (SITE_LINK, shout_type, post_id, etc, city)

    return link


def user_link(user):
    if not user or not isinstance(user, User):
        return None
    return "{0}{1}".format(SITE_LINK, user.username)


def tag_link(tag):
    if not isinstance(tag, (Tag, dict)):
        return None
    tag_name = tag.Name if hasattr(tag, 'Name') else tag['Name'] if 'Name' in tag else None
    if not tag_name:
        return None
    return "{0}tag/{1}/".format(SITE_LINK, tag_name)


def full_url_path(url):
    if isinstance(url, basestring):
        if url.startswith('/'):
            return SITE_LINK + url[1:]
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


cloud_connection = None


def get_cloud_connection():
    global cloud_connection
    if cloud_connection is None:
        pyrax.set_setting('identity_type', settings.CLOUD_IDENTITY)
        cloud_connection = pyrax.set_credentials(username=settings.CLOUD_USERNAME, api_key=settings.CLOUD_API_KEY)
    return cloud_connection


def cloud_upload_image(uploaded, container_name, filename, is_raw=True):
    try:
        cf = get_cloud_connection().cloudfiles
        container = cf.get_container(container_name)
        data = ''
        if is_raw:
            data = uploaded.body if hasattr(uploaded, 'body') else uploaded
        else:
            for c in uploaded.chunks():
                data += c
        filename = os.path.splitext(filename)[0] + '.jpg'
        buff = StringIO.StringIO()
        buff.write(data)
        buff.seek(0)
        image = Image.open(buff)
        if container.name == 'user_image':
            width, height = image.size
            if width != height:
                box = (0, 0, min(width, height), min(width, height))
                image = image.crop(box)
                image.format = "JPEG"
            image.thumbnail((220, 220), Image.ANTIALIAS)
        else:
            image.thumbnail((800, 600), Image.ANTIALIAS)
        
        buff = StringIO.StringIO()
        image.save(buff, format="JPEG", quality=80)
        buff.seek(0)
        obj = container.store_object(obj_name=filename, data=buff.buf, content_type=mimetypes.guess_type(filename))

        if container.name == 'user_image':
            make_cloud_thumbnails_for_user_image(obj.container.cdn_uri + '/' + obj.name)

        return obj
    except Exception, e:
        raise Http404(e.message)


def cloud_upload_file(uploaded, container, filename, is_raw):
    try:
        cf = get_cloud_connection().cloudfiles
        container = cf.get_container(container)
        data = ''
        if is_raw:
            data = uploaded.body
        else:
            for c in uploaded.chunks():
                data += c
        obj = container.store_object(obj_name=filename, data=data, content_type=mimetypes.guess_type(filename))
        return obj
    except Exception, e:
        print e
    return None


class NotAllowedUsernamesValidator(object):
    message = 'This username can not be used, please choose something else.'
    code = 'invalid'

    def __call__(self, value):
        if value in NOT_ALLOWED_USERNAMES:
            raise ValidationError(self.message, code=self.code)


validate_allowed_usernames = NotAllowedUsernamesValidator()
