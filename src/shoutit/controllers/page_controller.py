from __future__ import unicode_literals
from common.constants import USER_TYPE_PAGE

from shoutit.models import (User)
from shoutit.utils import generate_username


def create_page(creator, name, category, page_fields=None, **extra_user_fields):
    """
    """
    # Username
    username = extra_user_fields.pop('username', None)
    if not username:
        username = generate_username()
    while User.objects.filter(username=username).exists():
        username = generate_username()

    # Page fields
    page_fields = page_fields or {}
    page_fields.update({
        'creator': creator,
        'name': name,
        'category': category
    })

    # User fields
    extra_user_fields.update({
        'type': USER_TYPE_PAGE,
        'page_fields': page_fields
    })
    user = User.objects.create_user(username=username, **extra_user_fields)

    return user
