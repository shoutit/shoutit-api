from datetime import datetime
import random
import json
import os
import re
import urlparse
import uuid
import math
import base64
import hashlib
import hmac
import StringIO
import mimetypes

import Image
import pyrax
from django.http import HttpResponse, Http404
from numpy import array, argmax, sum, sqrt
from milk.unsupervised import _kmeans, kmeans as __kmeans
import numpy as np
from django.conf import settings

from common.constants import POST_TYPE_EXPERIENCE, POST_TYPE_REQUEST, POST_TYPE_OFFER
from apps.shoutit.models import Experience


def generate_password():
    return random_uuid_str()[24:]


def random_uuid_str():
    return str(uuid.uuid4())


def get_farest_point(observation, points):
    observation = array(observation)
    points = array(points)

    diff = points - observation
    dist = sqrt(sum(diff ** 2, axis=-1))
    farest_index = argmax(dist)
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


def number_of_clusters_based_on_zoom(zoom):
    if 3 <= zoom <= 4:
        return 15
    if 5 <= zoom <= 6:
        return 10
    if 7 <= zoom <= 8:
        return 8
    if 9 <= zoom <= 12:
        return 15
    if 13 <= zoom <= 14:
        return 20
    if 15 <= zoom <= 18:
        return 50
    return 0


def dist_function(f_matrix, cs):
    dists = np.dot(f_matrix, (-2) * cs.T)
    dists += np.array([np.dot(c, c) for c in cs])
    return dists


def kmeans(fmatrix, k, max_iter=1000):
    fmatrix = np.asanyarray(fmatrix)

    if fmatrix.dtype in (np.float32, np.float64) and fmatrix.flags['C_CONTIGUOUS']:
        computecentroids = _kmeans.computecentroids
    else:
        computecentroids = __kmeans._pycomputecentroids

    centroids = np.array(fmatrix[0:k], fmatrix.dtype)
    prev = np.zeros(len(fmatrix), np.int32)
    counts = np.empty(k, np.int32)
    dists = None
    for i in xrange(max_iter):
        dists = dist_function(fmatrix, centroids)
        assignments = dists.argmin(1)
        if np.all(assignments == prev):
            break
        if computecentroids(fmatrix, centroids, assignments.astype(np.int32), counts):
            (empty,) = np.where(counts == 0)
            centroids = np.delete(centroids, empty, axis=0)
            k = len(centroids)
            counts = np.empty(k, np.int32)
            # This will cause new matrices to be allocated in the next iteration
            dists = None
        prev[:] = assignments
    return assignments, centroids


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


from django.utils.decorators import available_attrs
from django.utils.functional import wraps


def asynchronous_task():
    def wrapper(f):
        try:
            @wraps(f, assigned=available_attrs(f))
            def _wrapper(*args, **kwargs):
                try:
                    # from celery.task.control import inspect
                    # insp = inspect()
                    # d = insp.active()
                    # if not d:
                    from libs.celery.celery_tasks_____asdasd import execute

                    execute.delay('', f.__module__, '', f.func_name, *args, **kwargs)
                except Exception, e:
                    print e
                    f(*args, **kwargs)

            _wrapper.func = f
            return _wrapper
        except Exception:
            return f

    return wrapper


@asynchronous_task()
def make_image_thumbnail(url, size, container_name):
    from Image import open as image_open, ANTIALIAS
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
        link = 'http%s://%s/%s-experience/%s/%s%s/' % (
            's' if settings.IS_SITE_SECURE else '', settings.SHOUT_IT_DOMAIN, experience_type, post_id, about, city)
    else:
        shout = post
        shout_type = 'request' if shout.Type == POST_TYPE_REQUEST else 'offer' if shout.Type == POST_TYPE_OFFER else 'shout'
        etc = to_seo_friendly(shout.Item.Name if hasattr(shout, 'Item') else shout.trade.Item.Name)
        city = to_seo_friendly(unicode.lower(shout.ProvinceCode))
        link = 'http%s://%s/%s/%s/%s-%s/' % ('s' if settings.IS_SITE_SECURE else '', settings.SHOUT_IT_DOMAIN, shout_type, post_id, etc, city)

    return link


def full_image_path(image_url):
    if isinstance(image_url, basestring):
        if image_url.startswith('/'):
            return 'http%s://%s%s' % ('s' if settings.IS_SITE_SECURE else '', settings.SHOUT_IT_DOMAIN, image_url)
    return image_url


class JsonResponse(HttpResponse):
    """
    An HTTP response class that consumes data to be serialized to JSON.
    """

    def __init__(self, data, **kwargs):
        kwargs.setdefault('content_type', 'application/json')
        data = json.dumps(data)
        super(JsonResponse, self).__init__(content=data, **kwargs)


class JsonResponseBadRequest(JsonResponse):
    status_code = 400


def get_cloud_connection():
    pyrax.set_setting('identity_type', settings.CLOUD_IDENTITY)
    pyrax.set_credentials(username=settings.CLOUD_USERNAME, api_key=settings.CLOUD_API_KEY)
    return pyrax
if not settings.OFFLINE_MODE:
    cloud_connection = get_cloud_connection()


def cloud_upload_image(uploaded, container_name, filename, is_raw=True):
    try:
        cf = cloud_connection.cloudfiles
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
        cf = cloud_connection.cloudfiles
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

