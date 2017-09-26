from common.constants import USER_TYPE_PAGE
from shoutit.controllers import user_controller

from shoutit.models import (User)
from shoutit.utils import generate_username


def create_page(creator, name, category, page_fields=None, **extra_user_fields):
    """
    """
    # Username
    username = extra_user_fields.pop('username', None)
    if not username:
        username = generate_username()
    while User.exists(username=username):
        username = generate_username()

    # Page fields
    page_fields = page_fields or {}
    if not page_fields.get('location'):
        page_fields.update(creator.location)
    page_fields.update({
        'creator': creator,
        'name': name,
        'category': category
    })

    # User fields
    extra_user_fields.update({
        'type': USER_TYPE_PAGE,
        'page_fields': page_fields,
        'is_activated': creator.is_activated
    })
    user = User.objects.create_user(username=username, **extra_user_fields)

    return user


def user_and_page_from_shoutit_page_data(data, initial_profile=None, is_test=False):
    # Todo (mo): use atomic transactions to make sure both page and user are created.
    # Create the user
    user = user_controller.user_from_shoutit_signup_data(data, initial_user=initial_profile, is_test=is_test)

    # Create the page
    name = data['page_name']
    category = data['page_category']
    page = create_page(creator=user, name=name, category=category)

    return user, page
