from __future__ import unicode_literals

from datetime import datetime

from django.db import IntegrityError
from django.utils.translation import ugettext_lazy as _
from rest_framework.exceptions import ValidationError as DRFValidationError

from common.constants import USER_TYPE_PROFILE, DEFAULT_LOCATION
from shoutit.api.v3.exceptions import ShoutitBadRequest
from shoutit.controllers import location_controller, media_controller
from shoutit.models import User, LinkedGoogleAccount, CLUser, DBUser, DBZ2User
from shoutit.utils import generate_username, debug_logger


def create_user(email=None, password=None, first_name='', last_name='', username=None, profile_fields=None,
                **extra_user_fields):
    # email
    if email and User.exists(email=email.lower()):
        raise DRFValidationError({'email': _('This email is used by another account')})

    # first, last and username
    if not username:
        username = generate_username()
    while len(username) < 2 or User.exists(username=username):
        username = generate_username()
    if first_name and len(first_name) < 2:
        first_name = ''
    if last_name and len(last_name) < 1:
        last_name = ''
    if not first_name:
        first_name = 'user'
    if not last_name:
        last_name = username
    username = username[:30]
    first_name = first_name[:30]
    last_name = last_name[:30]

    # profile fields
    profile_fields = profile_fields or {}
    if not location_controller.has_full_location(profile_fields):
        profile_fields.update(DEFAULT_LOCATION)
    extra_user_fields.update({
        'type': USER_TYPE_PROFILE,
        'profile_fields': profile_fields
    })
    user = User.objects.create_user(username=username, email=email, password=password, first_name=first_name,
                                    last_name=last_name, **extra_user_fields)
    return user


def user_from_shoutit_signup_data(signup_data, initial_user=None, is_test=False):
    email = signup_data.get('email')
    password = signup_data.get('password')
    first_name = signup_data.get('first_name')
    last_name = signup_data.get('last_name')
    username = initial_user.get('username')
    profile_fields = {}
    location = {}
    if initial_user:
        if initial_user.get('location'):
            location = initial_user.get('location')
            location_controller.add_predefined_city(location)
        elif initial_user.get('ip'):
            location = location_controller.from_ip(initial_user.get('ip'))
    profile_fields.update(location)
    return create_user(email=email, password=password, first_name=first_name, last_name=last_name, username=username,
                       is_test=bool(is_test), profile_fields=profile_fields)


def user_from_guest_data(initial_gust_user, is_test=False):
    profile_fields = {}
    location = {}
    if initial_gust_user.get('location'):
        location = initial_gust_user.get('location')
        location_controller.add_predefined_city(location)
    elif initial_gust_user.get('ip'):
        location = location_controller.from_ip(initial_gust_user.get('ip'))
    profile_fields.update(location)
    return create_user(is_test=bool(is_test), is_guest=True, profile_fields=profile_fields)


def auth_with_gplus(gplus_user, credentials, initial_user=None, is_test=False):
    email = gplus_user.get('emails')[0].get('value').lower()
    name = gplus_user.get('name', {})
    first_name = name.get('givenName')
    last_name = name.get('familyName')
    username = initial_user.get('username')
    gplus_id = gplus_user.get('id')
    gender = gplus_user.get('gender')
    profile_fields = {}
    location = {}
    if initial_user:
        if initial_user.get('location'):
            location = initial_user.get('location')
            location_controller.add_predefined_city(location)
        elif initial_user.get('ip'):
            location = location_controller.from_ip(initial_user.get('ip'))
    profile_fields.update(location)
    profile_fields.update({'gender': gender})

    try:
        user = User.objects.get(email=email)
        debug_logger.debug('Found user: {} with same email of gplus_user: {}'.format(user, gplus_id))
        if location:
            location_controller.update_profile_location(user.profile, location, add_pc=False)
    except User.DoesNotExist:
        user = create_user(email=email, first_name=first_name, last_name=last_name, username=username,
                           is_activated=True,
                           profile_fields=profile_fields, is_test=is_test)

    if not user.is_activated:
        user.activate()

    if not user.profile.gender and gender:
        user.profile.update(gender=gender)

    credentials_json = credentials.to_json()
    try:
        LinkedGoogleAccount.objects.create(user=user, credentials_json=credentials_json, gplus_id=gplus_id)
    except IntegrityError as e:
        raise ShoutitBadRequest(message=_("Could not access your Google account, try again later"),
                                developer_message=str(e))
    image_url = gplus_user['image']['url'].split('?')[0]
    media_controller.set_profile_media(user.profile, 'image', image_url)
    return user


def auth_with_facebook(fb_user, initial_user=None, is_test=False):
    email = fb_user.get('email').lower()
    first_name = fb_user.get('first_name')
    last_name = fb_user.get('last_name')
    facebook_id = fb_user.get('id')
    gender = fb_user.get('gender')
    birthday = fb_user.get('birthday')
    username = initial_user and initial_user.get('username')
    location = initial_user and initial_user.get('location')
    profile_fields = {}
    update_fields = []
    if location:
        location_controller.add_predefined_city(location)  # Todo (mo): are we still using this?
        profile_fields.update(location)
        update_fields += location.keys()
    if gender:
        profile_fields.update({'gender': gender})
        update_fields.append('gender')
    if birthday:
        birthday = datetime.strptime(birthday, "%d/%m/%Y").date()
        profile_fields.update({'birthday': birthday})
        update_fields.append('birthday')

    try:
        user = User.objects.filter(email=email).select_related('profile').first()
        if not user:
            raise User.DoesNotExist()
        profile = user.profile
        debug_logger.debug('Found user: %s with same email of fb_user: %s' % (user, facebook_id))
        if location:
            location_controller.update_object_location(profile, location, save=False)
        if gender:
            profile.gender = gender
        profile.save(update_fields=update_fields)

    except User.DoesNotExist:
        user = create_user(email=email, first_name=first_name, last_name=last_name, username=username,
                           is_activated=True, profile_fields=profile_fields, is_test=is_test)

    if not user.is_activated:
        user.activate()

    return user


def sign_up_sss4(email, location, dbcl_type='cl', db_link='', mobile=''):
    profile_fields = {}
    profile_fields.update(location)
    if mobile:
        profile_fields.update({'mobile': mobile})
    user = create_user(email, None, profile_fields=profile_fields)
    if dbcl_type == 'cl':
        dbcl_user = CLUser(user=user, cl_email=email)
    elif dbcl_type == 'dbz':
        dbcl_user = DBUser(user=user, db_link=db_link)
    else:
        dbcl_user = DBZ2User(user=user, db_link=db_link)
    dbcl_user.save()
    return user
