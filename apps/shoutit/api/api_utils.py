from common.constants import Constant


class JSONUrl(Constant):
    values = {}
    counter = 0


JSON_URL_USER_IMAGE_THUMBNAIL = JSONUrl('/xhr/user/%s/picture/50/')
JSON_URL_SHOUT_IMAGE_THUMBNAIL = JSONUrl('/xhr/tag/%s/picture/50/')
JSON_URL_TAG_IMAGE_THUMBNAIL = JSONUrl('/image/%s/100/')
JSON_URL_MARK_NOTIFICATION_AS_READ = JSONUrl('/notification/%s/read/')
JSON_URL_MARK_NOTIFICATION_AS_UNREAD = JSONUrl('/notification/%s/unread/')

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

    JSON_URL_USER_IMAGE_THUMBNAIL: JSON_URL_USER_IMAGE_THUMBNAIL,
    JSON_URL_TAG_IMAGE_THUMBNAIL: JSON_URL_TAG_IMAGE_THUMBNAIL,
    JSON_URL_SHOUT_IMAGE_THUMBNAIL: JSON_URL_SHOUT_IMAGE_THUMBNAIL,
    JSON_URL_MARK_NOTIFICATION_AS_READ: JSON_URL_MARK_NOTIFICATION_AS_READ,
    JSON_URL_MARK_NOTIFICATION_AS_UNREAD: JSON_URL_MARK_NOTIFICATION_AS_UNREAD,
}


def get_object_url(obj, extra_params=None):
    class_name = obj.__class__.__name__
    if obj is not None and class_name in api_urls:
        url_list = api_urls[class_name]
        url, params = url_list[0], list(url_list[1:])
        for i in range(len(params)):
            params[i] = getattr(obj, params[i])
        if extra_params:
            params.extend(extra_params)
        url = url % tuple(params)
        return url
    else:
        raise Exception('URL for object %s of type %s was not found.' % (str(obj), class_name))


def get_custom_url(json_url, *params):
    if json_url in api_urls:
        return str(api_urls[json_url]) % tuple(params)
    else:
        raise Exception('URL for %s was not found.' % str(json_url))