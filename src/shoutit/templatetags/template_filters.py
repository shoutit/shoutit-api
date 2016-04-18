# -*- coding: utf-8 -*-
"""

"""
from __future__ import unicode_literals
from django.utils.html import escape
from django.core.urlresolvers import reverse, NoReverseMatch
from django import template

register = template.Library()


@register.simple_tag
def auth_login(request):
    """
    Include a login snippet if REST framework's login view is in the URLconf.
    """
    try:
        login_url = reverse('rest_framework:login')
    except NoReverseMatch:
        return ''

    snippet = "<a id='_user' href='{href}?next={next}'>Log in</a>".format(href=login_url, next=escape(request.path))
    return snippet


@register.simple_tag
def auth_logout(request, user):
    """
    Include a logout snippet if REST framework's logout view is in the URLconf.
    """
    try:
        logout_url = reverse('rest_framework:logout')
    except NoReverseMatch:
        return '<a id="_user">{user}</a>'.format(user=user)

    snippet = '<a id="_user" href="{href}?next={next}" title="Log out">{user}</a>'

    return snippet.format(user=user, href=logout_url, next=escape(request.path))
