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

from django.core.exceptions import ObjectDoesNotExist

from numpy import array,argmax, sqrt, sum
from milk.unsupervised.normalise import zscore
from apps.shoutit import constants
from apps.shoutit.models import Post, Experience, PredefinedCity
from pygeoip import *
import pygeoip
from milk.unsupervised import _kmeans
import numpy as np
import apps.shoutit.settings as settings

BASE62_ALPHABET = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"

def IntToBase62(value):
    result = ''

    while value:
        result = BASE62_ALPHABET[value % 62] + result
        value /= 62

    if not result:
        result = '0'

    return result

def TimeInBase62():
    return IntToBase62(int(time.time()))

def GeneratePassword():
    return IntToBase62(uuid.uuid4().int)

def RandomBase62(length):
    r = random.Random()
    return ''.join([r.choice(BASE62_ALPHABET) for i in range(length)])

def Base62ToInt(value):
    result = 0
    if isinstance(value, int):
        value = str(value)
    for c in value:
        if c not in BASE62_ALPHABET:
            raise Exception("Invalide Base62 format.")
        else:
            result = result * 62 + BASE62_ALPHABET.index(c)

    return result

def EntityID(entity):
    return IntToBase62(entity.id)

import math

def get_farest_point(observation, points):
    observation = array(observation)
    points = array(points)

    diff = points - observation
    dist = sqrt(sum(diff**2, axis=-1))
    farest_index = argmax(dist)
    return farest_index

def normalized_distance(lat1, long1, lat2, long2):
    # Convert latitude and longitude to
    # spherical coordinates in radians.
    degrees_to_radians = math.pi/180.0

    # phi = 90 - latitude
    phi1 = (90.0 - float(lat1))*degrees_to_radians
    phi2 = (90.0 - float(lat2))*degrees_to_radians

    # theta = longitude
    theta1 = float(long1)*degrees_to_radians
    theta2 = float(long2)*degrees_to_radians

    # Compute spherical distance from spherical coordinates.

    # For two locations in spherical coordinates
    # (1, theta, phi) and (1, theta, phi)
    # cosine( arc length ) =
    #	sin phi sin phi' cos(theta-theta') + cos phi cos phi'
    # distance = rho * arc length

    cos = (math.sin(phi1)*math.sin(phi2)*math.cos(theta1 - theta2)+
           math.cos(phi1)*math.cos(phi2))
    if cos >= 1.0:
        return 0.0
    arc = math.acos( cos )

    # multiply the result by pi * radius of earth to get the actual distance(approx.)
    return arc / math.pi

def mutual_followings(StreamsCode1, StreamsCode2):
    return len(set([int(x) for x in StreamsCode1.split(',')]) & set([int(x) for x in StreamsCode2.split(',')]))

#		location_info = getLocationInfoBylatlng(latlong)
#		country = "None"
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


def getLocationInfoBylatlng(latlong):
    params = {"latlng":latlong, "sensor":"true"}
    try:
        urldata = urllib.urlencode(params)
        url = "https://maps.googleapis.com/maps/api/geocode/json" + "?" + urldata
        urlobj = urllib2.urlopen(url)
        data = urlobj.read()
        datadict = json.loads(data)
        if datadict["status"]== u"OK":
            results = datadict["results"]

            # the frist object of the results give the most specific info of the latlng
            address = results[0]['formatted_address']

            # last object of results give the country info object, and the one before give the city info object and country info object and so on >>>
            # level2_addressComponents the object before the last one
            level2_addressComponents = results[len(results)-2]['address_components']
            country = level2_addressComponents[len(level2_addressComponents)-1]['short_name']

            if len(level2_addressComponents)>=2:
                city = level2_addressComponents[len(level2_addressComponents)-2]['long_name']
            else:
                city = level2_addressComponents[len(level2_addressComponents)-1]['long_name']
            return {"address":address , "country":country , "city":city}
        else:
            return {"error":"Zero Results"}
    except Exception:
        return {"error":"exception"}


def getIP(request):
    ip = None
    if request:
        ip = request.META.get('HTTP_X_REAL_IP')
    if not ip or ip =='':
        ip = '80.227.53.34'
    return ip

def getLocationInfoByIP(request):
    #Get User IP
    ip = getIP(request)

    #Get Info(lat lng) By IP
    gi = GeoIP('libs/pygeoip/GeoIPCity.dat', pygeoip.MEMORY_CACHE)
    record = gi.record_by_addr(ip)  #168.144.92.219  82.137.200.83

    #another way to get locationInfo
#	ipInfo = IPInfo(apikey='0efaf242211014c381d34b89402833abb29bfaf2d6e2a6d5ef8268c0d2025e82')
#	locationInfo = ipInfo.GetIPInfo('http://api.ipinfodb.com/v3/ip-city/',ip = ip)
#	record = locationInfo.split(';')
#	result.data['location'] =  record[8] + ' ' + record[9]	#	"25.2644" + "+" + "55.3117"  #"33.5 + 36.4"

    if record and record.has_key('city'):
            return {"ip":ip, "country": record["country_code"] , "city": unicode(RemoveNonAscii(record["city"]))  , "latitude" : record['latitude'] , "longitude": record['longitude']}
#		else:
#			return {"ip":ip, "country": record["country_code"] , "c":record['country_name'] , "city":u'Dubai' , "latitude" : record['latitude'] , "longitude": record['longitude']}
    else:
        return {"ip":ip, "country": u'AE' , "city":u'Dubai' , "latitude" : 25.2644 , "longitude": 55.3117}


def numberOfClustersBasedOnZoom(zoom):
    if zoom >= 3 and zoom <= 4:
        return 15
    if zoom >= 5 and zoom <= 6:
        return 10
    if zoom >= 7 and zoom <= 8:
        return 8
    if zoom >= 9 and zoom <= 12:
        return 15
    if zoom >= 13 and zoom <= 14:
        return 20
    if zoom >= 15 and zoom <= 18:
        return 50
    return 0



def distfunction(fmatrix, cs):
    dists = np.dot(fmatrix, (-2)*cs.T)
    dists += np.array([np.dot(c,c) for c in cs])
    return dists

def kmeans(fmatrix, k , max_iter=1000):
    fmatrix = np.asanyarray(fmatrix)

    if fmatrix.dtype in (np.float32, np.float64) and fmatrix.flags['C_CONTIGUOUS']:
        computecentroids = _kmeans.computecentroids
    else:
        computecentroids = _pycomputecentroids


    centroids = np.array(fmatrix[0:k], fmatrix.dtype)
    prev = np.zeros(len(fmatrix), np.int32)
    counts = np.empty(k, np.int32)
    dists = None
    for i in xrange(max_iter):
        dists = distfunction(fmatrix, centroids)
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


def generateConfirmToken(type):
    ran = random.Random()
    return ''.join([ran.choice(type[0]) for i in range(0, type[1])])

def generateUsername():
    return str(random.randint(1000000000,1999999999))

def CorrectMobile(mobile):
    mobile = RemoveNonAscii(mobile)
    mobile = mobile.replace(' ','').replace('-','').replace('+','')
    if len(mobile) > 8:
        mobile = '971' + mobile[-9:]
    if len(mobile) == 12:
        return mobile
    else:
        return None

def RemoveNonAscii(s):
    return "".join(i for i in s if ord(i)<128)

def set_cookie(response, key, value, days_expire = 7):
    if days_expire is None:
        max_age = 365 * 24 * 60 * 60  #one year
    else:
        max_age = days_expire * 24 * 60 * 60
    expires = datetime.datetime.strftime(datetime.datetime.utcnow() + datetime.timedelta(seconds=max_age), "%a, %d-%b-%Y %H:%M:%S GMT")
    response.set_cookie(key, value, max_age=max_age, expires=expires, domain=settings.SESSION_COOKIE_DOMAIN, secure=settings.SESSION_COOKIE_SECURE or None)


import base64,hashlib,hmac
def base64_url_decode(inp):
    inp = inp.replace('-','+').replace('_','/')
    padding_factor = (4 - len(inp) % 4) % 4
    inp += "="*padding_factor
    return base64.decodestring(inp)

def parse_signed_request(signed_request='a.a', secret=settings.FACEBOOK_APP_SECRET):
    l = signed_request.split('.', 2)
    encoded_sig = l[0]
    payload = l[1]

    sig = base64_url_decode(encoded_sig)
    data = json.loads(base64_url_decode(payload))

    if data.get('algorithm').upper() != 'HMAC-SHA256':
#		print('Unknown algorithm')
        return None
    else:
        expected_sig = hmac.new(secret, msg=payload, digestmod=hashlib.sha256).digest()

    if sig != expected_sig:
        return None
    else:
#		print('valid signed request received..')
        return data


https_cdn = re.compile(r'http://((?:[\w-]+\.)+)(r\d{2})\.(.*)', re.IGNORECASE)
def get_https_cdn(url):
    m = https_cdn.match(url)
    if m:
        return 'https://%sssl.%s' % (m.group(1), m.group(3))
    else:
        return url

def safe_string(value):
    c = re.compile( '\\b' + ('%s|%s'%('\\b', '\\b')).join(settings.PROFANITIES_LIST) + '\\b', re.IGNORECASE)
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
    filename = '%s_%d%s' %(filename, size, extension)
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
                    from apps.shoutit.celery_tasks import execute
                    execute.delay('', f.__module__, '', f.func_name, *args, **kwargs)
                except Exception as e:
                    f(*args, **kwargs)
            _wrapper.func = f
            return _wrapper
        except Exception:
            return f
    return wrapper

@asynchronous_task()
def make_image_thumbnail(url, size, container):
    import cloudfiles
    import urlparse
    import os
    import Image
    import mimetypes
    import StringIO
    from django.core.files.base import ContentFile
    filename = os.path.basename(urlparse.urlparse(url)[2])
    content_type = mimetypes.guess_type(filename)
    name, extension = os.path.splitext(filename)
    connection = cloudfiles.get_connection(settings.CLOUD_FILES_AUTH, settings.CLOUD_FILES_KEY, servicenet = settings.CLOUD_FILES_SERVICE_NET)
    container = connection.get_container(container)
    file = container.get_object(filename)
    content_file = ContentFile(file.read())
    image = Image.open(content_file)
    thumb = image.copy()
    thumb.thumbnail((size, size), Image.ANTIALIAS)
    file = container.create_object('%s_%d%s' % (name, size, extension))
    file.content_type = content_type
    buff = StringIO.StringIO()
    thumb.save(buff, format = image.format)
    buff.seek(0)
    file.write(buff)

def ToSeoFriendly(s, maxlen=50):
    import re
    allowed_chars = ['-','.']
    t = '-'.join(s.split())                              			    # join words with dashes
    u = ''.join([c for c in t if c.isalnum() or c in allowed_chars])    # remove punctuation
    u = u[:maxlen].rstrip(''.join(allowed_chars)).lower()               # clip to maxlen
    u = re.sub(r'(['+r','.join(allowed_chars)+r'])\1+', r'\1', u)		# keep one occurrence of allowed chars
    return u


def ShoutLink(post):
    if not post:
        return None
    id = IntToBase62(post.pk)

    if post.Type == constants.POST_TYPE_EXPERIENCE:
        if post._meta.module_name == Post._meta.module_name:
            post = Experience.objects.get(pk=post.id)
        experience = post
        about = ToSeoFriendly(experience.AboutBusiness.name())

        city = ('-' + ToSeoFriendly(unicode.lower(experience.AboutBusiness.City))) if experience.AboutBusiness.City else ''
        type = 'bad' if experience.State == 0 else 'good'
        link = 'http%s://%s/%s-experience/%s/%s%s/'%('s' if settings.IS_SITE_SECURE else '', settings.SHOUT_IT_DOMAIN, type, id, about, city)
    else:
        shout = post
        type = 'request' if shout.Type == 0 else 'offer' if shout.Type == 1 else 'shout'
        etc = ToSeoFriendly(shout.Item.Name if hasattr(shout, 'Item') else shout.trade.Item.Name)
        city = ToSeoFriendly(unicode.lower(shout.ProvinceCode))
        link = 'http%s://%s/%s/%s/%s-%s/'%('s' if settings.IS_SITE_SECURE else '', settings.SHOUT_IT_DOMAIN, type, id, etc, city)

    return link

def IsSessionHasLocation(request):
    rs = request.session
    return True if (rs.has_key('user_lat') and rs.has_key('user_lng') and rs.has_key('user_country') and rs.has_key('user_city') and rs.has_key('user_city_encoded')) else False

def MapWithPredefinedCity(city):
    mapped_location = {}
    try:
        pdc = PredefinedCity.objects.get(City = city)
        mapped_location['latitude'] = pdc.Latitude
        mapped_location['longitude'] = pdc.Longitude
        mapped_location['country'] = pdc.Country
        mapped_location['city'] = pdc.City
        mapped_location['city_encoded'] = pdc.EncodedCity
    except ObjectDoesNotExist:
        mapped_location = {'latitude':25.2644,'longitude':55.3117,'country':u'AE','city':u'Dubai','city_encoded':'dubai'}

    return mapped_location