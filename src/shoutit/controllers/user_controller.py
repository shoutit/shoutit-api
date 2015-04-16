import urllib2
import boto
from django.utils.translation import ugettext as _
from django.conf import settings

from shoutit.models import User, Profile, ConfirmToken, LinkedFacebookAccount, UserPermission, Business, PredefinedCity, LinkedGoogleAccount, \
    CLUser, DBUser
from common.constants import *
from shoutit.utils import to_seo_friendly, generate_confirm_token, generate_username, generate_password
from shoutit.permissions import ConstantPermission, ACTIVATED_USER_PERMISSIONS, INITIAL_USER_PERMISSIONS
from shoutit.controllers import email_controller
import logging
logger = logging.getLogger('shoutit.warnings')


def get_profile(username):
    """
    return Profile or Business for the username
    """
    if not isinstance(username, basestring):
        return None
    try:
        q = Profile.objects.filter(user__username__iexact=username)
        if q:
            return q[0]
        else:
            q = Business.objects.filter(user__username__iexact=username)
            if q:
                return q[0]
            else:
                return None
    except ValueError, e:
        return None


def GetUserByEmail(email):
    if not isinstance(email, str) and not isinstance(email, unicode):
        return None
    try:
        q = User.objects.filter(email__iexact=email)
        if q:
            return q[0].abstract_profile
        else:
            return None
    except ValueError, e:
        return None


def set_last_token(user, email, token_length, token_type):
    token = generate_confirm_token(token_length)
    db_token = ConfirmToken.getToken(token)
    while db_token is not None:
        token = generate_confirm_token(token_length)
        db_token = ConfirmToken.getToken(token)
    tok = ConfirmToken(Token=token, user=user, Email=email, type=token_type)
    tok.save()
    profile = user.abstract_profile
    profile.LastToken = tok
    profile.save()
    return token


def GetUserByToken(token, get_disabled=True, case_sensitive=True):
    db_token = ConfirmToken.getToken(token, get_disabled, case_sensitive)
    if db_token is not None:
        return db_token.user
    else:
        return None


def ActivateUser(token, user):
    db_token = ConfirmToken.getToken(token)
    profile = user.abstract_profile
    if not profile:
        return None
    if db_token:
        profile.LastToken = None
        profile.save()
        db_token.delete()

    user.is_active = True
    user.save()
    return user


def SignUpUser(request, fname, lname, password, email=None, mobile=None, send_activation=True):
    if (email is None or email == '') and (mobile is None or mobile == ''):
        raise Exception(_('Signup parameters are not valid!'))

    if email is None or email == '':
        token_type = TOKEN_TYPE_HTML_NUM
        token_length = TOKEN_SHORT_UPPER
    else:
        token_type = TOKEN_TYPE_HTML_EMAIL
        token_length = TOKEN_LONG

    username = generate_username()
    while len(User.objects.filter(username=username)):
        username = generate_username()

    django_user = User.objects.create_user(username, email if email is not None else '', password)
    django_user.first_name = fname
    django_user.last_name = lname

    django_user.is_active = False
    django_user.save()

    up = Profile(user=django_user, Mobile=mobile)

    up.image = '/static/img/_user_male.png'
    up.save()

    encoded_city = to_seo_friendly(unicode.lower(unicode(up.city)))
    predefined_city = PredefinedCity.objects.filter(city=up.city)
    if not predefined_city:
            predefined_city = PredefinedCity.objects.filter(city_encoded=encoded_city)
    if not predefined_city:
        PredefinedCity(city=up.city, city_encoded=encoded_city, country=up.country, latitude=up.latitude, longitude=up.longitude).save()

    token = set_last_token(django_user, django_user.email, token_length, token_type)
    if email is not None and send_activation:
        email_controller.SendRegistrationActivationEmail(django_user, email, "http://%s%s" % (
            settings.SHOUT_IT_DOMAIN, '/' + token + '/'), token)
    django_user.token = token
    return django_user


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
        user=django_user, isSSS=True,
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


def CompleteSignUp(request, user, token, tokenType, username, email, mobile, sex, birthday=None):
    if mobile == '':
        mobile = None
    if email == '':
        email = None
    if email is not None:
        user.email = email
    user.username = username
    user.save()
    user.profile.Sex = sex
    user.profile.birthday = birthday
    if not sex:
        user.profile.image = '/static/img/_user_female.png'
    user.profile.save()

    if token is not None and len(token) > 0:
        ActivateUser(token, user)


def complete_signup(request, user, sex, birthday=None):
    user.profile.Sex = sex
    if not sex:
        user.profile.image = '/static/img/_user_female.png'
    user.profile.birthday = birthday or None
    if user.profile.LastToken:
        user.profile.LastToken.delete()
    user.profile.LastToken = None
    user.profile.save()
    user.is_active = True
    user.save()


def auth_with_gplus(request, gplus_user, credentials):
    user = User.objects.filter(email__iexact=gplus_user['emails'][0]['value'])
    user = user[0] if user else None
    gender = True if 'gender' in gplus_user and gplus_user['gender'] == 'male' else False

    if not user:
        password = generate_password()
        user = SignUpUser(request, fname=gplus_user['name']['givenName'], lname=gplus_user['name']['familyName'], password=password,
                          email=gplus_user['emails'][0]['value'], send_activation=False)
        CompleteSignUp(request, user=user, token=user.token, tokenType=TOKEN_TYPE_HTML_EMAIL, sex=gender,
                       email=gplus_user['emails'][0]['value'], username=user.username, mobile='')
        give_user_permissions(user, INITIAL_USER_PERMISSIONS + ACTIVATED_USER_PERMISSIONS)
    elif not user.is_active:
        complete_signup(request, user, gender)
        give_user_permissions(user, ACTIVATED_USER_PERMISSIONS)

    try:
        la = LinkedGoogleAccount(user=user, credentials_json=credentials.to_json(), gplus_id=gplus_user['id'])
        la.save()
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


def auth_with_facebook(request, fb_user, long_lived_token):
    user = User.objects.filter(email__iexact=fb_user['email'])
    user = user[0] if user else None

    gender = False if 'gender' in fb_user and fb_user['gender'] == 'female' else True

    if not user:
        # todo: better email validation
        if len(fb_user['email']) > 100:
            return None
        password = generate_password()
        user = SignUpUser(request, fname=fb_user['first_name'], lname=fb_user['last_name'], password=password, email=fb_user['email'],
                          send_activation=False)
        CompleteSignUp(request, user=user, token=user.token, tokenType=TOKEN_TYPE_HTML_EMAIL, sex=gender,
                       email=fb_user['email'], username=user.username, mobile='')
        give_user_permissions(user, INITIAL_USER_PERMISSIONS + ACTIVATED_USER_PERMISSIONS)
    elif not user.is_active:
        complete_signup(request, user, gender)
        give_user_permissions(user, ACTIVATED_USER_PERMISSIONS)

    try:
        la = LinkedFacebookAccount(user=user, facebook_id=fb_user['id'], AccessToken=long_lived_token['access_token'],
                                   ExpiresIn=long_lived_token['expires'])
        la.save()
    except Exception, e:
        logger.warn(str(e))
        return None

    try:
        response = urllib2.urlopen('https://graph.facebook.com/me/picture/?type=large&access_token=' + long_lived_token['access_token'],
                                   timeout=20)
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

    profile.latitude = location['latitude']
    profile.longitude = location['longitude']
    profile.city = location['city']
    profile.country = location['country']
    profile.save()

    try:
        PredefinedCity.objects.get(city=location['city'])
    except PredefinedCity.DoesNotExist:
        encoded_city = to_seo_friendly(unicode.lower(unicode(location['city'])))
        PredefinedCity(city=location['city'], city_encoded=encoded_city, country=location['country'], latitude=location['latitude'],
                       longitude=location['longitude']).save()

    return profile


def give_user_permissions(user, permissions):
    for permission in permissions:
        if isinstance(permission, ConstantPermission):
            permission = permission.permission
        UserPermission.objects.get_or_create(user=user, permission=permission)


def take_permissions_from_user(user, permissions):
    for permission in permissions:
        if isinstance(permission, ConstantPermission):
            permission = permission.permission
        UserPermission.objects.filter(user=user, permission=permission).delete()

