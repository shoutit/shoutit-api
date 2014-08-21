from apps.shoutit.models import *
from apps.shoutit.constants import Constant
from apps.shoutit.utils import *


class JSONUrl(Constant):
    values = {}
    counter = 0

JSON_URL_USER_IMAGE_THUMBNAIL = JSONUrl()
JSON_URL_SHOUT_IMAGE_THUMBNAIL = JSONUrl()
JSON_URL_TAG_IMAGE_THUMBNAIL = JSONUrl()
JSON_URL_MARK_NOTIFICATION_AS_READ = JSONUrl()
JSON_URL_MARK_NOTIFICATION_AS_UNREAD = JSONUrl()

urls = {
    UserProfile : ('/user/%s/', 'username'),
    User: ('/user/%s/', 'username'),
    Shout: ('/shout/%s/', 'pk|base62'),
    Trade: ('/shout/%s/', 'pk|base62'),
    StoredImage: ('/image/%s/', 'pk|base62'),
    Item: ('/item/%s/', 'pk|base62'),
    Store: ('/store/%s/', 'pk|base62'),
    Tag: ('/tag/%s/', 'Name'),
    Conversation : ('/message/%s/', 'pk|base62'),
    Experience: ('/experience/%s/', 'pk|base62'),

    JSON_URL_USER_IMAGE_THUMBNAIL: '/xhr/user/%s/picture/50/',
    JSON_URL_TAG_IMAGE_THUMBNAIL: '/xhr/tag/%s/picture/50/',
    JSON_URL_SHOUT_IMAGE_THUMBNAIL: '/image/%s/100/',
    JSON_URL_MARK_NOTIFICATION_AS_READ: '/notification/%s/read/',
    JSON_URL_MARK_NOTIFICATION_AS_UNREAD: '/notification/%s/unread/',
}


def get_object_url(obj, extra_params=[]):
    if obj is not None and urls.has_key(obj.__class__):
        url, params = urls[obj.__class__][0], list(urls[obj.__class__][1:])
        for i in range(len(params)):
            if params[i].endswith('|base62'):
                params[i] = IntToBase62(getattr(obj, params[i][:-7]))
            else:
                params[i] = getattr(obj, params[i])
        params.extend(extra_params)
        url = url % tuple(params)
        return url
    else:
        raise Exception('URL for object %s of type %s was not found.' % (str(obj), obj.__class__.__name__))


def get_custom_url(JSON_URL, *params):
    if urls.has_key(JSON_URL):
        return urls[JSON_URL] % tuple(params)
    else:
        raise Exception('URL for %s was not found.' % str(JSON_URL))