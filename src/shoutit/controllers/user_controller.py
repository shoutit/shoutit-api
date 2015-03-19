from itertools import chain

import os
from django.contrib.auth import login, authenticate, logout
from django.core.exceptions import ObjectDoesNotExist
from django.utils.translation import ugettext as _
from django.db.models.aggregates import Min
from django.db.models.query_utils import Q
from django.conf import settings

from shoutit.models import User, Event, Profile, ConfirmToken, Stream, LinkedFacebookAccount, FollowShip, UserPermission, Business, PredefinedCity, LinkedGoogleAccount, \
    Listen, CLUser, DBUser
from common.constants import *
from shoutit.utils import to_seo_friendly, generate_confirm_token, generate_username, generate_password, cloud_upload_image
from shoutit.permissions import ConstantPermission, ACTIVATED_USER_PERMISSIONS, INITIAL_USER_PERMISSIONS
from shoutit.controllers import event_controller, email_controller


def get_profile(username):
    """
    return Profile or Business for the username
    """
    if not isinstance(username, basestring):
        return None
    try:
        q = Profile.objects.filter(user__username__iexact=username).select_related()
        if q:
            return q[0]
        else:
            q = Business.objects.filter(user__username__iexact=username).select_related()
            if q:
                return q[0]
            else:
                return None
    except ValueError, e:
        return None


def list_users(query, start_index=0, end_index=30):

    related = ['profile', 'business']

    queries = query.split()
    users = User.objects
    filters = Q()
    for q in queries:
        filters |= Q(username__icontains=q)
        filters |= Q(first_name__icontains=q)
        filters |= Q(last_name__icontains=q)
        filters |= Q(email__iexact=q)
        filters |= Q(business__isnull=False, business__name__icontains=q)

    users = users.select_related(*related).filter(filters)[start_index:end_index]

    return users


def search_users(query, flag=int(USER_TYPE_INDIVIDUAL | USER_TYPE_BUSINESS), start_index=0, end_index=30, email_search=False):

    related = ['profile', 'business']

    is_email = query.count('@') > 0
    if is_email and email_search:
        users = User.objects.filter(email__iexact=query).select_related(*related)[start_index:end_index]
    else:
        queries = query.split()
        users = User.objects
        filters = Q()
        for q in queries:
            filters |= Q(first_name__icontains=q)
            filters |= Q(last_name__icontains=q)
            filters |= Q(business__isnull=False, business__name__icontains=q)
            if flag:
                if not (flag & int(USER_TYPE_INDIVIDUAL)):
                    filters &= Q(profile__isnull=True)
                if not (flag & int(USER_TYPE_BUSINESS)):
                    filters &= Q(business__isnull=True)

        users = users.select_related(*related).filter(filters)[start_index:end_index]

    user_profiles = []
    for user in users:
        user = user.abstract_profile
        if user:
            user_profiles.append(user)
    return user_profiles


def GetUserByEmail(email):
    if not isinstance(email, str) and not isinstance(email, unicode):
        return None
    try:
        q = User.objects.filter(email__iexact=email).select_related()
        if q:
            return q[0].abstract_profile
        else:
            return None
    except ValueError, e:
        return None


def GetUserByMobile(mobile):
    if not isinstance(mobile, str) and not isinstance(mobile, unicode):
        return None
    try:
        q = Profile.objects.filter(Mobile__iexact=mobile).select_related()
        if q:
            return q[0]
        else:
            return None
    except ValueError, e:
        return None


def SetRecoveryToken(user):
    token = generate_confirm_token(TOKEN_LONG)
    db_token = ConfirmToken.getToken(token)
    while db_token is not None:
        token = generate_confirm_token(TOKEN_LONG)
        db_token = ConfirmToken.getToken(token)
    tok = ConfirmToken(Token=token, user=user, type=TOKEN_TYPE_RECOVER_PASSWORD)
    tok.save()
    return token


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


def login_without_password(request, user):
    user.backend = 'django.contrib.auth.backends.ModelBackend'
    login(request, user)


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
    while len(User.objects.filter(username=username).select_related()):
        username = generate_username()

    django_user = User.objects.create_user(username, email if email is not None else '', password)
    django_user.first_name = fname
    django_user.last_name = lname

    django_user.is_active = False
    django_user.save()

    stream = Stream(type=STREAM_TYPE_USER)
    stream.save()

    up = Profile(user=django_user, Stream=stream, Mobile=mobile)

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
    SignInUser(request, password, username)
    django_user.token = token
    return django_user


def SignUpSSS(request, mobile, location, country, city):
    token_type = TOKEN_TYPE_HTML_NUM
    token_length = TOKEN_SHORT_UPPER

    username = generate_username()
    while len(User.objects.filter(username=username).select_related()):
        username = generate_username()

    password = generate_password()

    django_user = User.objects.create_user(username, "", password)
    django_user.is_active = False
    django_user.save()
    stream = Stream(type=STREAM_TYPE_USER)
    stream.save()

    up = Profile(user=django_user, Stream=stream, Mobile=mobile, isSSS=True)
    up.save()

    up.latitude = location[0]
    up.longitude = location[1]
    up.country = country
    up.city = city
    up.image = '/static/img/_user_male.png'
    up.save()

    if not PredefinedCity.objects.filter(city=up.city):
        encoded_city = to_seo_friendly(unicode.lower(unicode(up.city)))
        PredefinedCity(city=up.city, city_encoded=encoded_city, country=up.country, latitude=up.latitude, longitude=up.longitude).save()

    token = set_last_token(django_user, '', token_length, token_type)
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

    stream = Stream(type=STREAM_TYPE_USER)
    stream.save()
    up = Profile(
        user=django_user, Stream=stream, isSSS=True,
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


def CompleteSignUpSSS(request, first_name, last_name, password, user, username, token, tokenType, email, sex, birthday):
    if tokenType == TOKEN_TYPE_HTML_NUM:
        user.email = email
    user.first_name = first_name
    user.last_name = last_name
    if username and username.strip() != '':
        user.username = username
    if password is not None and password.strip() != '':
        user.set_password(password)
    user.save()
    user.profile.Sex = sex
    if not sex:
        user.profile.image = '/static/img/_user_female.png'
    user.profile.birthday = birthday
    user.profile.save()

    ActivateUser(token, user)


# todo: links
def ChangeEmailAndSendActivation(request, user, email):
    token = set_last_token(user, email, TOKEN_LONG, TOKEN_TYPE_HTML_EMAIL)
    email_controller.SendRegistrationActivationEmail(user, email, "http://%s%s" % (settings.SHOUT_IT_DOMAIN, '/' + token + '/'), token)


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


def SignUpUserFromAPI(request, first_name, last_name, username, email, password, sex, birthday, mobile=None):
    django_user = User.objects.create_user(username, email, password)
    django_user.first_name = first_name
    django_user.last_name = last_name
    django_user.is_active = False
    django_user.save()
    stream = Stream(type=STREAM_TYPE_USER)
    stream.save()
    up = Profile(user=django_user, Stream=stream, Mobile=mobile)
    up.birthday = birthday
    up.Sex = sex
    if not sex:
        up.image = '/static/img/_user_female.png'
    else:
        up.image = '/static/img/_user_male.png'
    up.save()
    return django_user


def ValidateCredentials(credential, password):
    list = User.objects.filter(username__iexact=credential)

    if not list:
        list = User.objects.filter(email__iexact=credential)

    if list:
        user = list[0]
    else:
        return None

    if user.check_password(password):
        return user
    else:
        return None


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
        give_user_permissions(None, INITIAL_USER_PERMISSIONS + ACTIVATED_USER_PERMISSIONS, user)
    elif not user.is_active:
        complete_signup(request, user, gender)
        give_user_permissions(None, ACTIVATED_USER_PERMISSIONS, user)

    try:
        la = LinkedGoogleAccount(user=user, credentials_json=credentials.to_json(), gplus_id=gplus_user['id'])
        la.save()
    except Exception, e:
        print 'LinkedGoogleAccount Error: ', str(e)
        return None

    if user.profile.image in ['/static/img/_user_male.png', '/static/img/_user_female.png']:
        try:
            import urllib2
            response = urllib2.urlopen(gplus_user['image']['url'].split('?')[0], timeout=20)
            data = response.read()
            filename = generate_password()
            obj = cloud_upload_image(data, 'user_image', filename, True)  # todo: images names as username
            user.profile.image = obj.container.cdn_uri + '/' + obj.name
            user.profile.save()

        except Exception, e:
            print 'auth_with_gplus profile.image error:', e.message
    return user


def auth_with_facebook(request, fb_user, long_lived_token):
    user = User.objects.filter(email__iexact=fb_user['email'])
    user = user[0] if user else None

    gender = False if 'gender' in fb_user and fb_user['gender'] == 'female' else True

    if not user:
        # todo: better email validation
        if len(fb_user['email']) > 75:
            return None
        password = generate_password()
        user = SignUpUser(request, fname=fb_user['first_name'], lname=fb_user['last_name'], password=password, email=fb_user['email'],
                          send_activation=False)
        CompleteSignUp(request, user=user, token=user.token, tokenType=TOKEN_TYPE_HTML_EMAIL, sex=gender,
                       email=fb_user['email'], username=user.username, mobile='')
        give_user_permissions(None, INITIAL_USER_PERMISSIONS + ACTIVATED_USER_PERMISSIONS, user)
    elif not user.is_active:
        complete_signup(request, user, gender)
        give_user_permissions(None, ACTIVATED_USER_PERMISSIONS, user)

    try:
        la = LinkedFacebookAccount(user=user, facebook_id=fb_user['id'], AccessToken=long_lived_token['access_token'],
                                   ExpiresIn=long_lived_token['expires'])
        la.save()
    except Exception, e:
        print str(e)
        return None

    if user.profile.image in ['/static/img/_user_male.png', '/static/img/_user_female.png']:
        try:
            import urllib2
            response = urllib2.urlopen('https://graph.facebook.com/me/picture/?type=large&access_token=' + long_lived_token['accessToken'],
                                       timeout=20)
            no_pic = ['yDnr5YfbJCH', 'HsTZSDw4avx']
            pic_file = os.path.splitext(response.geturl().split('/')[-1])

            if pic_file[0] not in no_pic and pic_file[1] != '.gif':  # todo: check if new changes to fb default profile pics
                data = response.read()
                filename = generate_password()
                obj = cloud_upload_image(data, 'user_image', filename, True)  # todo: images names as username
                user.profile.image = obj.container.cdn_uri + '/' + obj.name
                user.profile.save()

        except Exception, e:
            print e.message
            pass

    return user


def SignInUser(request, password, credential=''):
    user = ValidateCredentials(credential, password)
    if user:
        user = authenticate(username=user.username, password=password)
        if request:
            if user.abstract_profile:
                login(request, user)
            else:
                request.session['business_user_id'] = user.pk
            return user
        else:
            return None
    else:
        return None


def updatePassword(user, oldPassword, newPassword):
    if user.check_password(oldPassword):
        user.set_password(newPassword)
        return True
    else:
        return False


def SignOut(request):
    logout(request)


def UserFollowing(username, type='all', period='recent'):
    user = get_profile(username)
    result = {'users': [], 'tags': []}
    if period == 'recent':
        limit = 5
    elif period == 'all':
        limit = None
    else:
        limit = 0

    if type == 'users' or type == 'all':
        users = [f[0] for f in
                 FollowShip.objects.filter(follower__pk=user.pk, stream__type=STREAM_TYPE_USER).values_list('stream__user').order_by(
                     '-date_followed')[:limit]]
        result['users'] = [u for u in Profile.objects.all().filter(pk__in=users)]

    if type == 'tags' or type == 'all':
        result['tags'] = [f[0] for f in FollowShip.objects.filter(follower__pk=user.pk, stream__type=STREAM_TYPE_TAG).values_list(
            'stream__tag__name').order_by('-date_followed')[:limit]]

    return result


def is_listening(user, stream):
    try:
        Listen.objects.get(listener=user, stream=stream)
        return True
    except Listen.DoesNotExist:
        return False


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


def update_profile_attributes(profile, new_attributes):
    user = profile.user
    updated_user_fields = []
    updated_profile_fields = []

    if 'username' in new_attributes:
        user.username = new_attributes['username']
        updated_user_fields.append('username')

    if 'email' in new_attributes:
        user.email = new_attributes['email']
        updated_user_fields.append('email')

    if 'first_name' in new_attributes:
        user.first_name = new_attributes['first_name']
        updated_user_fields.append('first_name')

    if 'last_name' in new_attributes:
        user.last_name = new_attributes['last_name']
        updated_user_fields.append('last_name')

    if 'bio' in new_attributes:
        profile.Bio = new_attributes['bio']
        updated_profile_fields.append('Bio')

    if 'sex' in new_attributes:
        profile.Sex = new_attributes['sex']
        updated_profile_fields.append('Sex')

    user.save(update_fields=updated_user_fields)
    profile.save(update_fields=updated_profile_fields)

    return profile


# todo: use the give_user_permission
def give_user_permissions(request, permissions, user=None):
    if request and not user:
        user = request.user
    for permission in permissions:
        if isinstance(permission, ConstantPermission):
            permission = permission.permission
        UserPermission.objects.get_or_create(user=user, permission=permission)


def take_permissions_from_user(request, permissions):
    for permission in permissions:
        if isinstance(permission, ConstantPermission):
            permission = permission.permission
        UserPermission.objects.filter(user=request.user, permission=permission).delete()


def give_user_permission(request, permission):
    if isinstance(permission, ConstantPermission):
        permission = permission.permission
    UserPermission.objects.get_or_create(user=request.user, permission=permission)


def take_permission_from_user(request, permission):
    if isinstance(permission, ConstantPermission):
        permission = permission.permission
    UserPermission.objects.filter(user=request.user, permission=permission).delete()


def get_notifications(profile):
    if not hasattr(profile, 'notifications'):
        min_date = profile.user.notifications.filter(ToUser=profile.user, is_read=False).aggregate(min_date=Min('DateCreated'))['min_date']
        if min_date:
            notifications = list(profile.user.notifications.filter(DateCreated__gte=min_date).order_by('-DateCreated'))
            if len(notifications) < 5:
                notifications = sorted(
                    chain(notifications, list(
                        profile.user.notifications.filter(DateCreated__lt=min_date).order_by('-DateCreated')[:5 - len(notifications)])),
                    key=lambda n: n.DateCreated,
                    reverse=True
                )
        else:
            notifications = list(profile.user.notifications.filter(is_read=True).order_by('-DateCreated')[:5])
        profile.notifications = notifications
    return profile.notifications


def get_all_notifications(profile):
    if not hasattr(profile, 'all_notifications'):
        profile.all_notifications = list(profile.user.notifications.order_by('-DateCreated'))
    return profile.all_notifications


def get_unread_notifications_count(profile):
    notifications = hasattr(profile, 'notifications') and profile.notifications
    if not notifications:
        notifications = hasattr(profile, 'all_notifications') and profile.all_notifications
    if not notifications:
        notifications = get_notifications(profile)
    return len(filter(lambda n: not n.is_read, notifications))


def activities_stream(profile, start_index=None, end_index=None):
    stream_posts_query_set = profile.Stream.Posts.get_valid_posts([POST_TYPE_EVENT]).filter(
        ~Q(type=POST_TYPE_EVENT) |
        (Q(type=POST_TYPE_EVENT)
         & Q(event__is_disabled=False)
         & (Q(event__EventType=EVENT_TYPE_FOLLOW_USER) | Q(event__EventType=EVENT_TYPE_FOLLOW_BUSINESS) | Q(
            event__EventType=EVENT_TYPE_FOLLOW_TAG) | Q(event__EventType=EVENT_TYPE_SHARE_EXPERIENCE) | Q(
            event__EventType=EVENT_TYPE_COMMENT) | Q(event__EventType=EVENT_TYPE_BUY_DEAL))
        )
    ).order_by('-date_published')

    post_count = stream_posts_query_set.count()

    post_ids = [post['pk'] for post in stream_posts_query_set[start_index:end_index].values('pk')]
    #	trades = Trade.objects.get_valid_trades().filter(pk__in = post_ids).select_related('item','item__Currency','user','user__Profile','user__Business')
    #	trades = shout_controller.get_trade_images(trades)

    events = Event.objects.get_valid_events().filter(pk__in=post_ids).select_related('user', 'user__Profile').order_by(
        '-date_published')
    events = event_controller.GetDetailedEvents(events)
    #	stream_posts = sorted(chain( trades, events),key=lambda instance: instance.date_published,reverse = True)
    stream_posts = events

    return post_count, stream_posts