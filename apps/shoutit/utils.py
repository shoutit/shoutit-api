from datetime import datetime
import random
import json
import urllib
import urllib2
import os
import re
import urlparse
import time
import uuid
import math
import base64
import hashlib
import hmac
import Image
import StringIO

import mimetypes
import pyrax

from django.http import HttpResponse, Http404
from django.core.exceptions import ObjectDoesNotExist
from numpy import array, argmax, sqrt, sum
from pygeoip import GeoIP, MEMORY_CACHE
from milk.unsupervised import _kmeans, kmeans as __kmeans
import numpy as np
from django.conf import settings

from apps.shoutit import constants
from apps.shoutit.models import Post, Experience, PredefinedCity


BASE62_ALPHABET = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"


def int_to_base62(value):
    result = ''

    while value:
        result = BASE62_ALPHABET[value % 62] + result
        value /= 62

    if not result:
        result = '0'

    return result


def TimeInBase62():
    return int_to_base62(int(time.time()))


def generate_password():
    return int_to_base62(uuid.uuid4().int)


def random_base62(length):
    r = random.Random()
    return ''.join([r.choice(BASE62_ALPHABET) for i in range(length)])


def base62_to_int(value):
    result = 0
    if isinstance(value, int):
        value = str(value)
    for c in value:
        if c not in BASE62_ALPHABET:
            raise Exception("Invalide Base62 format.")
        else:
            result = result * 62 + BASE62_ALPHABET.index(c)

    return result


def entity_id(entity):
    return int_to_base62(entity.id)


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
    return len(set([int(x) for x in streams_code1.split(',')]) & set([int(x) for x in streams_code2.split(',')]))


# location_info = get_location_info_by_latlng(latlong)
# country = "None"
#		city = "None"
#		address = "None"
#		if not location_info.has_key("error"):
#			country = location_info["country"]
#			city = location_info["city"]
#			address = location_info["address"]
#		elif location_info["error"]=="Zero Results":
#			result.messages.append(('error', "Location Not Valid"))
#			result.errors.append(RESPONSE_RESULT_ERROR_BAD_REQUEST)
#			return result
#		else:
#			result.messages.append(('error', "Connection Error"))
#			result.errors.append(RESPONSE_RESULT_ERROR_BAD_REQUEST)
#			return result


def get_location_info_by_latlng(latlng):
    params = {"latlng": latlng, "sensor": "true"}
    try:
        urldata = urllib.urlencode(params)
        url = "https://maps.googleapis.com/maps/api/geocode/json?" + urldata
        urlobj = urllib2.urlopen(url)
        data = urlobj.read()
        datadict = json.loads(data)
        if datadict["status"] == u"OK":
            results = datadict["results"]

            # the first object of the results give the most specific info of the latlng
            address = results[0]['formatted_address']

            # last object of results give the country info object, and the one before give the city info object and country info object and so on >>>
            # level2_address_components the object before the last one
            level2_address_components = results[len(results) - 2]['address_components']
            country = level2_address_components[len(level2_address_components) - 1]['short_name']

            if len(level2_address_components) >= 2:
                city = level2_address_components[len(level2_address_components) - 2]['long_name']
            else:
                city = level2_address_components[len(level2_address_components) - 1]['long_name']
            return {"address": address, "country": country, "city": city}
        else:
            return {"error": "Zero Results"}
    except Exception:
        return {"error": "exception"}


def get_ip(request):
    ip = None
    if request:
        ip = request.META.get('HTTP_X_REAL_IP')
    if not ip or ip == '':
        ip = '80.227.53.34'
    return ip


def get_location_info_by_ip(request):
    # Get User IP
    ip = get_ip(request)

    # Get Info(lat lng) By IP
    # TODO Move gi initialization in a global scope so its done only once.
    gi = GeoIP(os.path.join(settings.BASE_DIR, 'libs', 'pygeoip') + '/GeoIPCity.dat', MEMORY_CACHE)
    record = gi.record_by_addr(ip)  #168.144.92.219  82.137.200.83

    #another way to get locationInfo
    #	ipInfo = IPInfo(apikey='0efaf242211014c381d34b89402833abb29bfaf2d6e2a6d5ef8268c0d2025e82')
    #	locationInfo = ipInfo.GetIPInfo('http://api.ipinfodb.com/v3/ip-city/',ip = ip)
    #	record = locationInfo.split(';')
    #	result.data['location'] =  record[8] + ' ' + record[9]	#	"25.2644" + "+" + "55.3117"  #"33.5 + 36.4"

    if record and 'city' in record:
        return {"ip": ip, "country": record["country_code"], "city": unicode(remove_non_ascii(record["city"])),
                "latitude": record['latitude'], "longitude": record['longitude']}
    #		else:
    #			return {"ip":ip, "country": record["country_code"] , "c":record['country_name'] , "city":u'Dubai' , "latitude" : record['latitude'] , "longitude": record['longitude']}
    else:
        return {"ip": ip, "country": u'AE', "city": u'Dubai', "latitude": 25.2644, "longitude": 55.3117}


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
                    #					from celery.task.control import inspect
                    #					insp = inspect()
                    #					d = insp.active()
                    #					if not d:
                    from libs.celery.celery_tasks_____asdasd import execute

                    execute.delay('', f.__module__, '', f.func_name, *args, **kwargs)
                except Exception as e:
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


def to_seo_friendly(s, max_len=50):
    import re

    allowed_chars = ['-', '.']
    t = '-'.join(s.split())  # join words with dashes
    u = ''.join([c for c in t if c.isalnum() or c in allowed_chars])  # remove punctuation
    u = u[:max_len].rstrip(''.join(allowed_chars)).lower()  # clip to max_len
    u = re.sub(r'([' + r','.join(allowed_chars) + r'])\1+', r'\1', u)  # keep one occurrence of allowed chars
    return u


def shout_link(post):
    if not post:
        return None
    post_id = int_to_base62(post.pk)

    if post.Type == constants.POST_TYPE_EXPERIENCE:
        if post._meta.module_name == Post._meta.module_name:
            post = Experience.objects.get(pk=post.id)
        experience = post
        about = to_seo_friendly(experience.AboutBusiness.name())

        city = ('-' + to_seo_friendly(unicode.lower(experience.AboutBusiness.City))) if experience.AboutBusiness.City else ''
        type = 'bad' if experience.State == 0 else 'good'
        link = 'http%s://%s/%s-experience/%s/%s%s/' % (
            's' if settings.IS_SITE_SECURE else '', settings.SHOUT_IT_DOMAIN, type, post_id, about, city)
    else:
        shout = post
        type = 'request' if shout.Type == 0 else 'offer' if shout.Type == 1 else 'shout'
        etc = to_seo_friendly(shout.Item.Name if hasattr(shout, 'Item') else shout.trade.Item.Name)
        city = to_seo_friendly(unicode.lower(shout.ProvinceCode))
        link = 'http%s://%s/%s/%s/%s-%s/' % ('s' if settings.IS_SITE_SECURE else '', settings.SHOUT_IT_DOMAIN, type, post_id, etc, city)

    return link


def is_session_has_location(request):
    rs = request.session
    return True if 'user_lat' in rs and 'user_lng' in rs and 'user_country' in rs and 'user_city' in rs and 'user_city_encoded' in rs else False


def map_with_predefined_city(city):
    mapped_location = {}
    try:
        pdc = PredefinedCity.objects.get(City=city)
        mapped_location['latitude'] = pdc.Latitude
        mapped_location['longitude'] = pdc.Longitude
        mapped_location['country'] = pdc.Country
        mapped_location['city'] = pdc.City
        mapped_location['city_encoded'] = pdc.EncodedCity
    except ObjectDoesNotExist:
        mapped_location = {'latitude': 25.2644, 'longitude': 55.3117, 'country': u'AE', 'city': u'Dubai', 'city_encoded': 'dubai'}

    return mapped_location


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
        image.save(buff, format="JPEG", quality=60)
        buff.seek(0)
        obj = container.store_object(obj_name=filename, data=buff.buf, content_type=mimetypes.guess_type(filename))

        if container.name == 'user_image':
            make_image_thumbnail(obj.container.cdn_uri + '/' + obj.name, 95, 'user_image')
            make_image_thumbnail(obj.container.cdn_uri + '/' + obj.name, 32, 'user_image')

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
        pass
    return None
