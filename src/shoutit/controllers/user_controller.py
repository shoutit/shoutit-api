from __future__ import unicode_literals
from django.core.exceptions import ValidationError
from django.db import IntegrityError
import requests
from rest_framework.exceptions import ValidationError as DRFValidationError
from shoutit.api.v2.exceptions import FB_LINK_ERROR_TRY_AGAIN, GPLUS_LINK_ERROR_TRY_AGAIN

from shoutit.models import (User, LinkedFacebookAccount, PredefinedCity,
                            LinkedGoogleAccount, CLUser, DBUser, DBZ2User)
from shoutit.utils import generate_username, debug_logger, error_logger, set_profile_image, \
    location_from_ip


def signup_user(email=None, password=None, first_name='', last_name='', username=None,
                profile_fields=None, **extra_user_fields):
    if email and User.objects.filter(email=email.lower()).exists():
        raise DRFValidationError({'email': "User with same email exists."})
    username = username or generate_username()
    while len(username) < 2 and User.objects.filter(username=username).exists():
        username = generate_username()
    if len(first_name) < 2:
        first_name = ''
    if len(last_name) < 1:
        last_name = ''
    if not first_name:
        first_name = 'user'
    if not last_name:
        last_name = username
    extra_user_fields.update({'profile_fields': profile_fields})
    user = User.objects.create_user(username=username, email=email, password=password,
                                    first_name=first_name, last_name=last_name, **extra_user_fields)

    # used to later track signup events
    user.new_signup = True
    return user


def user_from_shoutit_signup_data(signup_data, initial_user=None):
    email = signup_data.get('email')
    password = signup_data.get('password')
    first_name = signup_data.get('first_name')
    last_name = signup_data.get('last_name')
    profile_fields = {}
    location = {}
    if initial_user:
        if initial_user.get('location'):
            location = initial_user.get('location')
            add_predefined_city(location)
        elif initial_user.get('ip'):
            location = location_from_ip(initial_user.get('ip'))
    profile_fields.update(location)
    return signup_user(email=email, password=password, first_name=first_name, last_name=last_name,
                       profile_fields=profile_fields)


def auth_with_gplus(gplus_user, credentials, initial_user=None):
    email = gplus_user.get('emails')[0].get('value').lower()
    name = gplus_user.get('name')
    first_name = name.get('givenName')
    last_name = name.get('familyName')
    gplus_id = gplus_user.get('id')
    gender = gplus_user.get('gender')
    profile_fields = {}
    location = {}
    if initial_user:
        if initial_user.get('location'):
            location = initial_user.get('location')
            add_predefined_city(location)
        elif initial_user.get('ip'):
            location = location_from_ip(initial_user.get('ip'))
    profile_fields.update(location)
    profile_fields.update({'gender': gender})

    try:
        user = User.objects.get(email=email)
        debug_logger.debug('Found user: {} with same email of gplus_user: {}'.format(user, gplus_id))
        if location:
            update_profile_location(user.profile, location, add_pc=False)
    except User.DoesNotExist:
        user = signup_user(email=email, first_name=first_name, last_name=last_name,
                           is_activated=True, profile_fields=profile_fields)

    if not user.is_activated:
        user.activate()

    if not user.profile.gender and gender:
        user.profile.update(gender=gender)

    credentials_json = credentials.to_json()
    try:
        la = LinkedGoogleAccount(user=user, credentials_json=credentials_json, gplus_id=gplus_id)
        la.save()
    except (ValidationError, IntegrityError) as e:
        print "create g+ la error", str(e)
        raise GPLUS_LINK_ERROR_TRY_AGAIN

    set_profile_image(user.profile, gplus_user['image']['url'].split('?')[0])
    return user


def auth_with_facebook(fb_user, long_lived_token, initial_user=None):
    email = fb_user.get('email').lower()
    first_name = fb_user.get('first_name')
    last_name = fb_user.get('last_name')
    username = fb_user.get('username')
    facebook_id = fb_user.get('id')
    gender = fb_user.get('gender')
    profile_fields = {}
    location = {}
    if initial_user:
        if initial_user.get('location'):
            location = initial_user.get('location')
            add_predefined_city(location)
        elif initial_user.get('ip'):
            location = location_from_ip(initial_user.get('ip'))
    profile_fields.update(location)
    profile_fields.update({'gender': gender})

    try:
        user = User.objects.get(email=email)
        debug_logger.debug('Found user: {} with same email of fb_user: {}'.format(user, facebook_id))
        if location:
            update_profile_location(user.profile, location, add_pc=False)
    except User.DoesNotExist:
        user = signup_user(email=email, first_name=first_name, last_name=last_name,
                           username=username, is_activated=True, profile_fields=profile_fields)

    if not user.is_activated:
        user.activate()

    if not user.profile.gender and gender:
        user.profile.update(gender=gender)

    access_token = long_lived_token.get('access_token')
    expires = long_lived_token.get('expires')
    try:
        la = LinkedFacebookAccount(user=user, facebook_id=facebook_id, access_token=access_token,
                                   expires=expires)
        la.save()
    except (ValidationError, IntegrityError) as e:
        error_logger.warn(str(e))
        raise FB_LINK_ERROR_TRY_AGAIN

    # todo: move the entire logic to rq
    std_male = '10354686_10150004552801856_220367501106153455_n.jpg'
    std_female = '1379841_10150004552801901_469209496895221757_n.jpg'
    image_url = 'https://graph.facebook.com/me/picture/?type=large&access_token=' + access_token
    try:
        response = requests.get(image_url, timeout=10)
        image_data = response.content
        if not (std_male in response.url or std_female in response.url or '.gif' in response.url):
            set_profile_image(user.profile, image_data=image_data)
    except requests.RequestException as e:
        error_logger.warn(str(e))

    return user


def sign_up_sss4(email, lat, lng, city, country, dbcl_type='cl', db_link=''):
    location = {
        'country': country,
        'city': city,
        'latitude': float(lat),
        'longitude': float(lng)
    }
    user = signup_user(email, None, profile_fields=location)
    if dbcl_type == 'cl':
        dbcl_user = CLUser(user=user, cl_email=email)
    elif dbcl_type == 'dbz':
        dbcl_user = DBUser(user=user, db_link=db_link)
    else:
        dbcl_user = DBZ2User(user=user, db_link=db_link)
    dbcl_user.save()
    return user


def update_profile_location(profile, location, add_pc=True, notify=True):
    # determine whether the profile should send a notification about its location changes
    setattr(profile, 'notify', notify)
    update_object_location(profile, location)
    if profile.country and profile.city and add_pc:
        add_predefined_city(location)


def add_predefined_city(location):
    try:
        pc = PredefinedCity()
        update_object_location(pc, location)
    except (ValidationError, IntegrityError):
        pass


def update_object_location(obj, location):
    obj.latitude = location.get('latitude')
    obj.longitude = location.get('longitude')
    obj.country = location.get('country', '')
    obj.postal_code = location.get('postal_code', '')
    obj.state = location.get('state', '')
    obj.city = location.get('city', '')
    obj.address = location.get('address', '')
    # if obj already exits, only save location attributes otherwise save everything
    if obj.created_at:
        obj.save(update_fields=['latitude', 'longitude', 'country', 'postal_code', 'state', 'city', 'address'])
    else:
        obj.save()
