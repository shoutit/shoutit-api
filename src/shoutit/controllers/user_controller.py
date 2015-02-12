from itertools import chain

import os
from django.contrib.auth import login, authenticate, logout
from django.core.exceptions import ObjectDoesNotExist
from django.utils.translation import ugettext as _
from django.db.models.aggregates import Min
from django.db.models.query_utils import Q
from django.conf import settings

from shoutit.models import User, Event, Profile, ConfirmToken, Stream, LinkedFacebookAccount, FollowShip, UserPermission, Business, PredefinedCity, LinkedGoogleAccount, \
    Listen, CLUser, DBCLUser
from activity_logger.logger import Logger
from common.constants import *
from shoutit.utils import to_seo_friendly, generate_confirm_token, generate_username, generate_password, cloud_upload_image
from shoutit.permissions import ConstantPermission, permissions_changed, ACTIVATED_USER_PERMISSIONS, INITIAL_USER_PERMISSIONS
from shoutit.controllers import event_controller, email_controller, notifications_controller


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


# todo: start index, limit, user/profile mix
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
            filters |= Q(business__isnull=False, business__Name__icontains=q)
            if flag:
                if not (flag & int(USER_TYPE_INDIVIDUAL)):
                    filters &= Q(profile__isnull=True)
                if not (flag & int(USER_TYPE_BUSINESS)):
                    filters &= Q(business__isnull=True)

        users = users.select_related(*related).filter(filters)[start_index:end_index]

    user_profiles = []
    for user in users:
        user = GetProfile(user)
        if user:
            user_profiles.append(user)
    return user_profiles


def GetProfile(user):
    try:
        if not isinstance(user, User):
            return None
        try:
            try:
                profile = user.profile
                if not profile:
                    raise ObjectDoesNotExist()
                return profile
            except ObjectDoesNotExist, e:
                try:
                    business = user.Business
                    if not business:
                        raise ObjectDoesNotExist()
                    return business
                except ObjectDoesNotExist, e:
                    return None
        except ValueError, e:
            return None
    except Exception, e:
        return None


def GetUserByEmail(email):
    if not isinstance(email, str) and not isinstance(email, unicode):
        return None
    try:
        q = User.objects.filter(email__iexact=email).select_related()
        if q:
            return GetProfile(q[0])
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
    tok = ConfirmToken(Token=token, user=user, Type=TOKEN_TYPE_RECOVER_PASSWORD)
    tok.save()
    return token


def SetRegisterToken(user, email, token_length, token_type):
    token = generate_confirm_token(token_length)
    db_token = ConfirmToken.getToken(token)
    while db_token is not None:
        token = generate_confirm_token(token_length)
        db_token = ConfirmToken.getToken(token)
    tok = ConfirmToken(Token=token, user=user, Email=email, Type=token_type)
    tok.save()
    profile = GetProfile(user)
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
    profile = GetProfile(user)
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

    stream = Stream(Type=STREAM_TYPE_USER)
    stream.save()

    up = Profile(user=django_user, Stream=stream, Mobile=mobile)

    up.image = '/static/img/_user_male.png'
    up.save()

    encoded_city = to_seo_friendly(unicode.lower(unicode(up.City)))
    predefined_city = PredefinedCity.objects.filter(City=up.City)
    if not predefined_city:
            predefined_city = PredefinedCity.objects.filter(city_encoded=encoded_city)
    if not predefined_city:
        PredefinedCity(City=up.City, city_encoded=encoded_city, Country=up.Country, Latitude=up.Latitude, Longitude=up.Longitude).save()

    Logger.log(request, type=ACTIVITY_TYPE_SIGN_UP, data={ACTIVITY_DATA_USERNAME: username})
    token = SetRegisterToken(django_user, django_user.email, token_length, token_type)
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
    stream = Stream(Type=STREAM_TYPE_USER)
    stream.save()

    up = Profile(user=django_user, Stream=stream, Mobile=mobile, isSSS=True)
    up.save()

    up.Latitude = location[0]
    up.Longitude = location[1]
    up.Country = country
    up.City = city
    up.image = '/static/img/_user_male.png'
    up.save()

    if not PredefinedCity.objects.filter(City=up.City):
        encoded_city = to_seo_friendly(unicode.lower(unicode(up.City)))
        PredefinedCity(City=up.City, city_encoded=encoded_city, Country=up.Country, Latitude=up.Latitude, Longitude=up.Longitude).save()

    Logger.log(request, type=ACTIVITY_TYPE_SIGN_UP, data={ACTIVITY_DATA_USERNAME: username})
    token = SetRegisterToken(django_user, '', token_length, token_type)
    django_user.token = token

    return django_user


def sign_up_sss4(email, lat, lng, city, country, dbcl_type='cl'):
    token_type = TOKEN_TYPE_HTML_NUM
    token_length = TOKEN_SHORT_UPPER

    username = generate_username()
    while len(User.objects.filter(username=username)):
        username = generate_username()

    password = generate_password()

    django_user = User.objects.create_user(username, email, password)
    django_user.is_active = False
    django_user.save()

    if dbcl_type == 'cl':
        dbcl_model = CLUser
    else:
        dbcl_model = DBCLUser

    dbcl_user = dbcl_model(user=django_user)
    dbcl_user.save()

    stream = Stream(Type=STREAM_TYPE_USER)
    stream.save()

    up = Profile(
        user=django_user, Stream=stream, isSSS=True,
        Latitude=lat, Longitude=lng, City=city, Country=country,
        image='/static/img/_user_male.png'
    )
    up.save()

    if not PredefinedCity.objects.filter(City=up.City):
        encoded_city = to_seo_friendly(unicode.lower(unicode(up.City)))
        PredefinedCity(City=up.City, city_encoded=encoded_city, Country=up.Country, Latitude=up.Latitude, Longitude=up.Longitude).save()

    token = SetRegisterToken(django_user, email, token_length, token_type)
    django_user.token = token

    return django_user


def CompleteSignUpSSS(request, firstname, lastname, password, user, username, token, tokenType, email, sex, birthday):
    if tokenType == TOKEN_TYPE_HTML_NUM:
        user.email = email
    user.first_name = firstname
    user.last_name = lastname
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
    token = SetRegisterToken(user, email, TOKEN_LONG, TOKEN_TYPE_HTML_EMAIL)
    email_controller.SendRegistrationActivationEmail(user, email,
                                                                              "http://%s%s" % (settings.SHOUT_IT_DOMAIN, '/' + token + '/'),
                                                                              token)


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
    from shoutit.controllers import realtime_controller as realtime_controller

    realtime_controller.BindUserToCity(user.username, user.profile.City)
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
    stream = Stream(Type=STREAM_TYPE_USER)
    stream.save()
    up = Profile(user=django_user, Stream=stream, Mobile=mobile)
    up.birthday = birthday
    up.Sex = sex
    if not sex:
        up.image = '/static/img/_user_female.png'
    else:
        up.image = '/static/img/_user_male.png'
    up.save()
    Logger.log(request, type=ACTIVITY_TYPE_SIGN_UP, data={ACTIVITY_DATA_USERNAME: username})
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


def auth_with_facebook(request, fb_user, auth_response):
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
        la = LinkedFacebookAccount(user=user, facebook_id=fb_user['id'], AccessToken=auth_response['accessToken'], ExpiresIn=auth_response['expiresIn'])
        la.save()
    except Exception, e:
        print e.message
        return None

    if user.profile.image in ['/static/img/_user_male.png', '/static/img/_user_female.png']:
        try:
            import urllib2
            response = urllib2.urlopen('https://graph.facebook.com/me/picture/?type=large&access_token=' + auth_response['accessToken'],
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
            if GetProfile(user):
                login(request, user)
            else:
                request.session['business_user_id'] = user.pk
            Logger.log(request, type=ACTIVITY_TYPE_SIGN_IN_SUCCESS)
            return user
        else:
            return None
    else:
        Logger.log(request, type=ACTIVITY_TYPE_SIGN_IN_FAILED, data={ACTIVITY_DATA_CREDENTIAL: credential})
        return None


def updatePassword(user, oldPassword, newPassword):
    if user.check_password(oldPassword):
        user.set_password(newPassword)
        return True
    else:
        return False


def SignOut(request):
    logout(request)
    Logger.log(request, type=ACTIVITY_TYPE_SIGN_OUT)


def FollowStream(request, follower, followed):
    if isinstance(follower, unicode):
        follower = get_profile(follower)
        if not follower:
            raise ObjectDoesNotExist()
    if follower.Stream == followed:
        return
    if followed not in follower.Following.all():
        followShip = FollowShip(follower=follower, stream=followed)
        followShip.save()
        Logger.log(request, type=ACTIVITY_TYPE_LISTEN_CREATED,
                   data={ACTIVITY_DATA_FOLLOWER: follower.username, ACTIVITY_DATA_STREAM: followed.pk})
        if followed.Type == STREAM_TYPE_USER:
            followedUser = Profile.objects.get(Stream=followed)
            email_controller.SendListenEmail(follower.user, followedUser.user)
            notifications_controller.notify_user_of_listen(followedUser.user, follower.user)
            event_controller.register_event(request.user, EVENT_TYPE_FOLLOW_USER, followedUser)
        elif followed.Type == STREAM_TYPE_BUSINESS:
            followedUser = Business.objects.get(Stream=followed)
            email_controller.SendListenEmail(follower.user, followedUser.user)
            notifications_controller.notify_user_of_listen(followedUser.user, follower.user)
            event_controller.register_event(request.user, EVENT_TYPE_FOLLOW_BUSINESS, followedUser)


def UnfollowStream(request, follower, followed):
    if isinstance(follower, unicode):
        follower = get_profile(follower)
        if not follower:
            raise ObjectDoesNotExist()
    if followed in follower.Following.all():
        followShip = FollowShip.objects.get(follower=follower, stream=followed)
        followShip.delete()
        Logger.log(request, type=ACTIVITY_TYPE_LISTEN_REMOVED,
                   data={ACTIVITY_DATA_FOLLOWER: follower.username, ACTIVITY_DATA_STREAM: followed.pk})


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
                 FollowShip.objects.filter(follower__pk=user.pk, stream__Type=STREAM_TYPE_USER).values_list('stream__OwnerUser').order_by(
                     '-date_followed')[:limit]]
        result['users'] = [u for u in Profile.objects.all().filter(pk__in=users)]

    if type == 'tags' or type == 'all':
        result['tags'] = [f[0] for f in FollowShip.objects.filter(follower__pk=user.pk, stream__Type=STREAM_TYPE_TAG).values_list(
            'stream__OwnerTag__Name').order_by('-date_followed')[:limit]]

    return result


def is_listening(user, stream):
    try:
        Listen.objects.get(listener=user, stream=stream)
        return True
    except Listen.DoesNotExist:
        return False


def update_profile_location(profile, location):

    profile.Latitude = location['latitude']
    profile.Longitude = location['longitude']
    profile.City = location['city']
    profile.Country = location['country']
    profile.save()

    try:
        PredefinedCity.objects.get(City=location['city'])
    except PredefinedCity.DoesNotExist:
        encoded_city = to_seo_friendly(unicode.lower(unicode(location['city'])))
        PredefinedCity(City=location['city'], city_encoded=encoded_city, Country=location['country'], Latitude=location['latitude'],
                       Longitude=location['longitude']).save()

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
    if request:
        permissions_changed.send(sender=None, request=request, permissions=permissions)


def take_permissions_from_user(request, permissions):
    for permission in permissions:
        if isinstance(permission, ConstantPermission):
            permission = permission.permission
        UserPermission.objects.filter(user=request.user, permission=permission).delete()
    permissions_changed.send(sender=None, request=request, permissions=permissions)


def give_user_permission(request, permission):
    if isinstance(permission, ConstantPermission):
        permission = permission.permission
    UserPermission.objects.get_or_create(user=request.user, permission=permission)
    permissions_changed.send(sender=None, request=request, permissions=[permission])


def take_permission_from_user(request, permission):
    if isinstance(permission, ConstantPermission):
        permission = permission.permission
    UserPermission.objects.filter(user=request.user, permission=permission).delete()
    permissions_changed.send(sender=None, request=request, permissions=[permission])


def get_notifications(profile):
    if not hasattr(profile, 'notifications'):
        min_date = profile.user.Notifications.filter(ToUser=profile.user, IsRead=False).aggregate(min_date=Min('DateCreated'))['min_date']
        if min_date:
            notifications = list(profile.user.Notifications.filter(DateCreated__gte=min_date).order_by('-DateCreated'))
            if len(notifications) < 5:
                notifications = sorted(
                    chain(notifications, list(
                        profile.user.Notifications.filter(DateCreated__lt=min_date).order_by('-DateCreated')[:5 - len(notifications)])),
                    key=lambda n: n.DateCreated,
                    reverse=True
                )
        else:
            notifications = list(profile.user.Notifications.filter(IsRead=True).order_by('-DateCreated')[:5])
        profile.notifications = notifications
    return profile.notifications


def get_all_notifications(profile):
    if not hasattr(profile, 'all_notifications'):
        profile.all_notifications = list(profile.user.Notifications.order_by('-DateCreated'))
    return profile.all_notifications


def get_unread_notifications_count(profile):
    notifications = hasattr(profile, 'notifications') and profile.notifications
    if not notifications:
        notifications = hasattr(profile, 'all_notifications') and profile.all_notifications
    if not notifications:
        notifications = get_notifications(profile)
    return len(filter(lambda n: not n.IsRead, notifications))


def activities_stream(profile, start_index=None, end_index=None):
    stream_posts_query_set = profile.Stream.Posts.get_valid_posts([POST_TYPE_EVENT]).filter(
        ~Q(Type=POST_TYPE_EVENT) |
        (Q(Type=POST_TYPE_EVENT)
         & Q(event__IsDisabled=False)
         & (Q(event__EventType=EVENT_TYPE_FOLLOW_USER) | Q(event__EventType=EVENT_TYPE_FOLLOW_BUSINESS) | Q(
            event__EventType=EVENT_TYPE_FOLLOW_TAG) | Q(event__EventType=EVENT_TYPE_SHARE_EXPERIENCE) | Q(
            event__EventType=EVENT_TYPE_COMMENT) | Q(event__EventType=EVENT_TYPE_BUY_DEAL))
        )
    ).order_by('-DatePublished')

    post_count = stream_posts_query_set.count()

    post_ids = [post['pk'] for post in stream_posts_query_set[start_index:end_index].values('pk')]
    #	trades = Trade.objects.get_valid_trades().filter(pk__in = post_ids).select_related('Item','Item__Currency','OwnerUser','OwnerUser__Profile','OwnerUser__Business')
    #	trades = shout_controller.get_trade_images(trades)

    events = Event.objects.get_valid_events().filter(pk__in=post_ids).select_related('OwnerUser', 'OwnerUser__Profile').order_by(
        '-DatePublished')
    events = event_controller.GetDetailedEvents(events)
    #	stream_posts = sorted(chain( trades, events),key=lambda instance: instance.DatePublished,reverse = True)
    stream_posts = events

    return post_count, stream_posts