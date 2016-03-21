# -*- coding: utf-8 -*-
"""

"""
from __future__ import unicode_literals
from django.core.urlresolvers import reverse


class UserLinkMixin(object):
    def _user(self, obj):
        return user_link(obj.user)
    _user.allow_tags = True
    _user.short_description = 'User'


class LinksMixin(object):
    def _links(self, obj):
        return links(obj)
    _links.allow_tags = True
    _links.short_description = 'Link'


class LocationMixin(object):
    def _location(self, obj):
        location = obj.location
        location_html = "%s,%s" % (location['latitude'], location['longitude'])
        location_html += "<br>c: %s | z: %s" % (location['country'], location['postal_code'])
        location_html += "<br>s: %s | c: %s" % (location['state'], location['city'])
        return location_html
    _location.allow_tags = True
    _location.short_description = 'Location'


def links(obj):
    web_link = '<a href="%s" target="_blank">%s</a>' % (obj.web_url, 'WebApp')
    # api_link = '<a href="%s" target="_blank">%s</a>' % (obj.api_url, 'Api')
    # return "%s | %s" % (web_link, api_link)
    return "%s" % web_link


def tag_link(tag):
    tag_url = reverse('admin:shoutit_tag_change', args=(tag.pk,))
    return '<a href="%s">%s</a>' % (tag_url, tag.name)


def user_link(user):
    if not user:
        return 'system'
    user_url = reverse('admin:shoutit_user_change', args=(user.pk,))
    return '<a href="%s">%s</a>' % (user_url, user.name_username)


def item_link(item):
    if not item:
        return 'no item'
    item_url = reverse('admin:shoutit_item_change', args=(item.pk,))
    return '<a href="%s">%s</a>' % (item_url, unicode(item))


def reply_link(conversation, user):
    message_add_url = reverse('admin:shoutit_message_add')
    params = '?conversation=%s&user=%s' % (conversation.pk, user.pk)
    return '<a href="%s%s">send reply</a>' % (message_add_url, params)
