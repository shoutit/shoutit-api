from common.constants import Constant
from settings import SITE_LINK


class JSONUrl(Constant):
    values = {}
    counter = 0


JSON_URL_MARK_NOTIFICATION_AS_READ = JSONUrl('/notifications/%s/read/')
JSON_URL_MARK_NOTIFICATION_AS_UNREAD = JSONUrl('/notifications/%s/unread/')

api_urls = {
    'User': ('/users/%s/', 'username'),
    'Profile': ('/users/%s/', 'username'),
    'Business': ('/users/%s/', 'username'),
    'Shout': ('/shouts/%s/', 'pk'),
    'Trade': ('/shouts/%s/', 'pk'),
    'StoredImage': ('/images/%s/', 'pk'),
    'item': ('/items/%s/', 'pk'),
    'Tag': ('/tags/%s/', 'name'),
    'Conversation': ('/messages/%s/', 'pk'),
    'Conversation2': ('/messages2/%s/', 'pk'),
    'Experience': ('/experiences/%s/', 'pk'),

    JSON_URL_MARK_NOTIFICATION_AS_READ: JSON_URL_MARK_NOTIFICATION_AS_READ,
    JSON_URL_MARK_NOTIFICATION_AS_UNREAD: JSON_URL_MARK_NOTIFICATION_AS_UNREAD,
}


api2_urls = {
    'User': ('users/{}', 'username'),
    'Profile': ('users/{}', 'username'),
    'Business': ('users/{}', 'username'),
    'Shout': ('shouts/{}', 'pk'),
    'Trade': ('shouts/{}', 'pk'),
    'StoredImage': ('images/{}', 'pk'),
    'item': ('items/{}', 'pk'),
    'Tag': ('tags/{}', 'name'),
    'Conversation2': ('messages2/{}', 'pk'),
    'Experience': ('experiences/{}', 'pk'),

    JSON_URL_MARK_NOTIFICATION_AS_READ: JSON_URL_MARK_NOTIFICATION_AS_READ,
    JSON_URL_MARK_NOTIFICATION_AS_UNREAD: JSON_URL_MARK_NOTIFICATION_AS_UNREAD,
}


def get_object_api_url(obj, extra_params=None):
    class_name = obj.__class__.__name__
    if obj is not None and class_name in api_urls:
        url_list = api_urls[class_name]
        url, params = url_list[0], list(url_list[1:])
        for i in range(len(params)):
            params[i] = getattr(obj, params[i])
        if extra_params:
            params.extend(extra_params)
        url = url % tuple(params)
        return SITE_LINK + 'api' + url
    else:
        raise Exception('URL for object %s of type %s was not found.' % (str(obj), class_name))


def get_api2_url(obj):
    class_name = obj.__class__.__name__
    if obj is not None and class_name in api2_urls:
        url_tuple = api2_urls[class_name]
        obj_url, pk_field = url_tuple[0], url_tuple[1]
        url = obj_url.format(getattr(obj, pk_field))
        return "{}api/v2/{}".format(SITE_LINK, url)
    else:
        raise Exception('URL for object %s of type %s was not found.' % (str(obj), class_name))


def get_custom_url(json_url, *params):
    if json_url in api_urls:
        return SITE_LINK + 'api' + str(api_urls[json_url]) % tuple(params)
    else:
        raise Exception('URL for %s was not found.' % str(json_url))