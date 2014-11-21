from apps.shoutit.constants import Constant
from apps.shoutit.utils import int_to_base62


class JSONUrl(Constant):
    values = {}
    counter = 0


JSON_URL_USER_IMAGE_THUMBNAIL = JSONUrl()
JSON_URL_SHOUT_IMAGE_THUMBNAIL = JSONUrl()
JSON_URL_TAG_IMAGE_THUMBNAIL = JSONUrl()
JSON_URL_MARK_NOTIFICATION_AS_READ = JSONUrl()
JSON_URL_MARK_NOTIFICATION_AS_UNREAD = JSONUrl()

api_urls = {
    'User': ('/user/%s/', 'username'),
    'Profile': ('/user/%s/', 'username'),
    'Business': ('/user/%s/', 'username'),
    'Shout': ('/shout/%s/', 'pk'),
    'Trade': ('/shout/%s/', 'pk'),
    'StoredImage': ('/image/%s/', 'pk'),
    'Item': ('/item/%s/', 'pk'),
    'Tag': ('/tag/%s/', 'Name'),
    'Conversation': ('/message/%s/', 'pk'),
    'Experience': ('/experience/%s/', 'pk'),

    JSON_URL_USER_IMAGE_THUMBNAIL: '/xhr/user/%s/picture/50/',
    JSON_URL_TAG_IMAGE_THUMBNAIL: '/xhr/tag/%s/picture/50/',
    JSON_URL_SHOUT_IMAGE_THUMBNAIL: '/image/%s/100/',
    JSON_URL_MARK_NOTIFICATION_AS_READ: '/notification/%s/read/',
    JSON_URL_MARK_NOTIFICATION_AS_UNREAD: '/notification/%s/unread/',
}


def get_object_url(obj, extra_params=None):
    class_name = obj.__class__.__name__
    if obj is not None and class_name in api_urls:
        url_list = api_urls[class_name]
        url, params = url_list[0], list(url_list[1:])
        for i in range(len(params)):
            if params[i].endswith('|base62'):
                params[i] = int_to_base62(getattr(obj, params[i][:-7]))
            else:
                params[i] = getattr(obj, params[i])
        if extra_params:
            params.extend(extra_params)
        url = url % tuple(params)
        return url
    else:
        raise Exception('URL for object %s of type %s was not found.' % (str(obj), class_name))


def get_custom_url(json_url, *params):
    if json_url in api_urls:
        return api_urls[json_url] % tuple(params)
    else:
        raise Exception('URL for %s was not found.' % str(json_url))