from common.constants import Constant
from django.conf import settings


class JSONUrl(Constant):
    values = {}
    counter = 0


JSON_URL_MARK_NOTIFICATION_AS_READ = JSONUrl('/notifications/%s/read/')
JSON_URL_MARK_NOTIFICATION_AS_UNREAD = JSONUrl('/notifications/%s/unread/')

api2_urls = {
    'User': ('users/{}', 'username'),
    'Profile': ('users/{}', 'username'),
    'Business': ('users/{}', 'username'),
    'Shout': ('shouts/{}', 'pk'),
    'item': ('items/{}', 'pk'),
    'Tag': ('tags/{}', 'name'),
    'Conversation': ('conversations/{}', 'pk'),
    'Experience': ('experiences/{}', 'pk'),

    JSON_URL_MARK_NOTIFICATION_AS_READ: JSON_URL_MARK_NOTIFICATION_AS_READ,
    JSON_URL_MARK_NOTIFICATION_AS_UNREAD: JSON_URL_MARK_NOTIFICATION_AS_UNREAD,
}


def get_api2_url(obj):
    class_name = obj.__class__.__name__
    if obj is not None and class_name in api2_urls:
        url_tuple = api2_urls[class_name]
        obj_url, pk_field = url_tuple[0], url_tuple[1]
        url = obj_url.format(getattr(obj, pk_field))
        return "{}v2/{}".format(settings.SITE_LINK, url)
    else:
        raise Exception('URL for object %s of type %s was not found.' % (str(obj), class_name))


def get_current_uri(request):
    """
    Builds an absolute URI from the variables available in this request ignoring query params.
    """
    return '%s://%s%s' % (request.scheme, request.get_host(), request.path)