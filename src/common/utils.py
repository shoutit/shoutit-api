"""
Utils that are independent of Apps and their models
"""
import sys
import re
from datetime import datetime
import httplib2


def get_address_port(using_gunicorn=False):
    if using_gunicorn:
        from etc.gunicorn_settings import bind
        return bind.split(':')

    if len(sys.argv) > 1 and sys.argv[1] == "runserver":
        address_port = sys.argv[-1] if len(sys.argv) > 2 else "127.0.0.1:8000"
        if address_port.startswith("-"):
            return
        else:
            try:
                address, port = address_port.split(':')
            except ValueError:
                address, port = '', address_port
        if not address:
            address = '127.0.0.1'
        return address, port

    else:
        return '127.0.0.1', '8000'


def check_offline_mood():
    http = httplib2.Http()
    try:
        resp, content = http.request('http://www.google.com')
        return False
    except httplib2.ServerNotFoundError:
        return True


def process_tags(tags):
    if not isinstance(tags, list):
        return []
    processed_tags = []
    for tag in tags:
        if not isinstance(tag, basestring):
            continue
        tag = tag.lower()
        tag = re.sub('[^a-z0-9-]', '', tag)
        tag = re.sub('([-]){2,}', '-', tag)
        tag = tag[1:] if tag.startswith('-') else tag
        tag = tag[0:-1] if tag.endswith('-') else tag

        if len(tag) >= 2:
            processed_tags.append(tag)
    return processed_tags


def date_unix(date):
    return int((date - datetime(1970, 1, 1)).total_seconds())
