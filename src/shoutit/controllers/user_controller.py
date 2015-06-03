from __future__ import unicode_literals
import urllib2
import boto
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from rest_framework.exceptions import ValidationError as DRFValidationError
from shoutit.api.v2.exceptions import FB_LINK_ERROR_TRY_AGAIN, GPLUS_LINK_ERROR_TRY_AGAIN

from shoutit.models import (User, LinkedFacebookAccount, PredefinedCity,
                            LinkedGoogleAccount, CLUser, DBUser, DBZ2User)
from shoutit.utils import generate_username
import logging

warn_logger = logging.getLogger('shoutit.warnings')
logger = logging.getLogger('shoutit.debug')


def sign_up_sss4(email, lat, lng, city, country, dbcl_type='cl', db_link=''):
    user = signup_user(email, None)
    if dbcl_type == 'cl':
        dbcl_user = CLUser(user=user, cl_email=email)
    elif dbcl_type == 'dbz':
        dbcl_user = DBUser(user=user, db_link=db_link)
    else:
        dbcl_user = DBZ2User(user=user, db_link=db_link)
    dbcl_user.save()

    profile = user.profile
    location = {
        'country': country,
        'city': city,
        'latitude': float(lat),
        'longitude': float(lng)
    }
    update_profile_location(profile, location)
    return user


def signup_user(email=None, password=None, first_name='', last_name='', username=None, **kwargs):
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
    return User.objects.create_user(username=username, email=email, password=password,
                                    first_name=first_name, last_name=last_name, **kwargs)


def user_from_shoutit_signup_data(signup_data):
    email = signup_data.get('email')
    password = signup_data.get('password')
    first_name = signup_data.get('first_name')
    last_name = signup_data.get('last_name')
    return signup_user(email=email, password=password, first_name=first_name, last_name=last_name)


def auth_with_gplus(gplus_user, credentials):
    email = gplus_user.get('emails')[0].get('value').lower()
    name = gplus_user.get('name')
    first_name = name.get('givenName')
    last_name = name.get('familyName')
    gplus_id = gplus_user.get('id')

    try:
        user = User.objects.get(email=email)
        logger.debug('Found user: {} with same email of gplus_user: {}'.format(user, gplus_id))
    except User.DoesNotExist:
        user = signup_user(email=email, first_name=first_name, last_name=last_name, is_activated=True)

    if not user.is_activated:
        user.activate()
        gender = gplus_user.get('gender')
        user.profile.update(gender=gender)

    credentials_json = credentials.to_json()
    try:
        la = LinkedGoogleAccount(user=user, credentials_json=credentials_json, gplus_id=gplus_id)
        la.save()
    except (ValidationError, IntegrityError) as e:
        print "create g+ la error", str(e)
        raise GPLUS_LINK_ERROR_TRY_AGAIN

    try:
        response = urllib2.urlopen(gplus_user['image']['url'].split('?')[0], timeout=20)
        # todo: check when pic is the std pic
        s3 = boto.connect_s3(settings.AWS_ACCESS_KEY_ID, settings.AWS_SECRET_ACCESS_KEY)
        bucket = s3.get_bucket('shoutit-user-image-original')
        img_data = response.read()
        filename = user.pk + '.jpg'
        key = bucket.new_key(filename)
        key.set_metadata('Content-Type', 'image/jpg')
        key.set_contents_from_string(img_data)
        s3_image_url = 'https://user-image.static.shoutit.com/%s' % filename
        user.profile.image = s3_image_url
        user.profile.save()
    except Exception, e:
        warn_logger.warn(str(e))

    return user


def auth_with_facebook(fb_user, long_lived_token):
    email = fb_user.get('email').lower()
    first_name = fb_user.get('first_name')
    last_name = fb_user.get('last_name')
    username = fb_user.get('username')
    facebook_id = fb_user.get('id')

    try:
        user = User.objects.get(email=email)
        logger.debug('Found user: {} with same email of fb_user: {}'.format(user, facebook_id))
    except User.DoesNotExist:
        user = signup_user(email=email, first_name=first_name, last_name=last_name,
                           username=username, is_activated=True)

    if not user.is_activated:
        user.activate()
        gender = fb_user.get('gender')
        user.profile.update(gender=gender)

    access_token = long_lived_token.get('access_token')
    expires = long_lived_token.get('expires')
    try:
        la = LinkedFacebookAccount(user=user, facebook_id=facebook_id, access_token=access_token,
                                   expires=expires)
        la.save()
    except (ValidationError, IntegrityError) as e:
        warn_logger.warn(str(e))
        raise FB_LINK_ERROR_TRY_AGAIN

    try:
        response = urllib2.urlopen('https://graph.facebook.com/me/picture/?type=large&access_token=' + access_token, timeout=20)
        std_male = '10354686_10150004552801856_220367501106153455_n.jpg'
        std_female = '1379841_10150004552801901_469209496895221757_n.jpg'
        response_url = response.geturl()
        if not (std_male in response_url or std_female in response_url or '.gif' in response_url):
            s3 = boto.connect_s3(settings.AWS_ACCESS_KEY_ID, settings.AWS_SECRET_ACCESS_KEY)
            bucket = s3.get_bucket('shoutit-user-image-original')
            img_data = response.read()
            filename = user.pk + '.jpg'
            key = bucket.new_key(filename)
            key.set_metadata('Content-Type', 'image/jpg')
            key.set_contents_from_string(img_data)
            s3_image_url = 'https://user-image.static.shoutit.com/%s' % filename
            user.profile.image = s3_image_url
            user.profile.save()
    except Exception, e:
        warn_logger.warn(str(e))

    return user


def update_profile_location(profile, location):
    update_object_location(profile, location)
    if profile.country and (profile.postal_code or profile.city):
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
    if obj.created_at:
        obj.save(update_fields=['latitude', 'longitude', 'country', 'postal_code', 'state', 'city', 'address'])
    else:
        obj.save()
