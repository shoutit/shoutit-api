import urllib2
import boto
from django.conf import settings

from shoutit.models import User, Profile, LinkedFacebookAccount, PredefinedCity, LinkedGoogleAccount, CLUser, DBUser
from common.constants import *
from shoutit.utils import to_seo_friendly, generate_username, generate_password
import logging

logger = logging.getLogger('shoutit.warnings')


def sign_up_sss4(email, lat, lng, city, country, dbcl_type='cl', db_link=''):
    username = generate_username()
    while len(User.objects.filter(username=username)):
        username = generate_username()
    password = generate_password()
    django_user = User.objects.create_user(username, email, password)
    django_user.is_active = False
    django_user.save()

    if dbcl_type == 'cl':
        dbcl_user = CLUser(user=django_user, cl_email=email)
    else:
        dbcl_user = DBUser(user=django_user, db_link=db_link)
    dbcl_user.save()

    up = Profile(
        user=django_user,
        latitude=lat, longitude=lng, city=city, country=country,
        image='/static/img/_user_male.png'
    )
    up.save()

    if not PredefinedCity.objects.filter(city=up.city):
        encoded_city = to_seo_friendly(unicode.lower(unicode(up.city)))
        PredefinedCity(city=up.city, city_encoded=encoded_city, country=up.country, latitude=up.latitude, longitude=up.longitude).save()

    token_type = TOKEN_TYPE_HTML_NUM
    token_length = TOKEN_SHORT_UPPER
    token = set_last_token(django_user, email, token_length, token_type)
    django_user.token = token
    return django_user


def signup_user(email, password, first_name='', last_name=''):
    username = generate_username()
    while User.objects.filter(username=username).exists():
        username = generate_username()
    user = User.objects.create_user(username=username, email=email, password=password, first_name=first_name, last_name=last_name)

    # todo: email verification
    # email_controller.SendRegistrationActivationEmail()
    return user


def user_from_shoutit_signup_data(signup_data):
    email = signup_data.get('email')
    password = signup_data.get('password')
    first_name = signup_data.get('first_name')
    last_name = signup_data.get('last_name')
    return signup_user(email=email, password=password, first_name=first_name, last_name=last_name)


def auth_with_gplus(gplus_user, credentials):
    email = gplus_user.get('emails')[0].get('value')
    password = generate_password()
    name = gplus_user.get('name')
    first_name = name.get('givenName')
    last_name = name.get('familyName')

    try:
        user = User.objects.get(email__iexact=email)
    except User.DoesNotExist:
        user = signup_user(email=email, password=password, first_name=first_name, last_name=last_name)

    if not user.is_activated:
        user.activate()
        gender = gplus_user.get('gender')
        user.profile.update(gender=gender)

    gplus_id = gplus_user.get('id')
    credentials_json = credentials.to_json()
    try:
        LinkedGoogleAccount.objects.create(user=user, credentials_json=credentials_json, gplus_id=gplus_id)
    except Exception, e:
        print 'LinkedGoogleAccount Error: ', str(e)
        return None

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
        s3_image_url = key.generate_url(expires_in=0, query_auth=False)
        user.profile.image = s3_image_url
        user.profile.save()
    except Exception, e:
        logger.warn(str(e))

    return user


def auth_with_facebook(fb_user, long_lived_token):
    email = fb_user.get('email')
    password = generate_password()
    first_name = fb_user.get('first_name')
    last_name = fb_user.get('last_name')

    try:
        user = User.objects.get(email__iexact=email)
    except User.DoesNotExist:
        user = signup_user(email=email, password=password, first_name=first_name, last_name=last_name)

    if not user.is_activated:
        user.activate()
        gender = fb_user.get('gender')
        user.profile.update(gender=gender)

    facebook_id = fb_user.get('id')
    access_token = long_lived_token.get('access_token')
    expires = long_lived_token.get('expires')
    try:
        LinkedFacebookAccount.objects.create(user=user, facebook_id=facebook_id, access_token=access_token, expires=expires)
    except Exception, e:
        logger.warn(str(e))
        return None

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
            s3_image_url = key.generate_url(expires_in=0, query_auth=False)
            user.profile.image = s3_image_url
            user.profile.save()
    except Exception, e:
        logger.warn(str(e))

    return user


def update_profile_location(profile, location):
    country = location['country']
    city = location['city']
    latitude = location['latitude']
    longitude = location['longitude']

    profile.latitude = latitude
    profile.longitude = longitude
    profile.city = city
    profile.country = country
    profile.save(update_fields=['country', 'city', 'latitude', 'longitude'])

    try:
        PredefinedCity.objects.get(city=city)
    except PredefinedCity.DoesNotExist:
        encoded_city = to_seo_friendly(unicode.lower(unicode(city)))
        PredefinedCity.objects.create(city=city, city_encoded=encoded_city, country=country, latitude=latitude, longitude=longitude)
    return profile
