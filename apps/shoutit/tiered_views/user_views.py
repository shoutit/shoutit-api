from django.contrib.auth.decorators import login_required
from django.http import HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
import math
import json
from apps.shoutit.permissions import PERMISSION_ACTIVATED, PERMISSION_FOLLOW_USER, INITIAL_USER_PERMISSIONS, ACTIVATED_USER_PERMISSIONS
from apps.shoutit.utils import ToSeoFriendly
from django.utils.translation import ugettext_lazy as _
from apps.shoutit.controllers import email_controller, realtime_controller
from apps.shoutit.controllers import stream_controller
from apps.shoutit.controllers import facebook_controller
from apps.shoutit.controllers.gplus_controller import user_from_gplus_code
from apps.shoutit.forms import *
from apps.shoutit.models import *
from apps.shoutit.tiered_views.renderers import *
from apps.shoutit.tiered_views.validators import *
from apps.shoutit.tiers import *
from apps.shoutit.constants import *
import urllib2


def urlencode(s):
    return urllib2.quote(s)


def urldecode(s):
    return urllib2.unquote(s).decode('utf8')


@non_cached_view(methods=['POST'],
                 api_renderer=operation_api,
                 validator=activate_api_validator,
                 login_required=True)
def activate_api(request, token):
    result = ResponseResult()

    form = ExtenedSignUp(request.POST, request.FILES,
                         initial={'email': request.user.email, 'tokentype': TOKEN_TYPE_API_EMAIL.value})
    form.is_valid()

    t = ConfirmToken.getToken(token, False, False)

    if not t:
        result.errors.append(RESPONSE_RESULT_ERROR_BAD_REQUEST)
        return result

    t.disable()

    source_email = None
    if t.Email and t.Email.strip() != '':
        source_email = t.Email
    email = form.cleaned_data['email']
    if source_email is not None:
        email = source_email

    user_controller.CompleteSignUp(request, request.user, token, t.Type, form.cleaned_data['username'], email,
                                   form.cleaned_data['mobile'], bool(int(form.cleaned_data['sex'])), form.cleaned_data['birthdate'])
    result.messages.append(('success', _('You are now activated.')))
    user_controller.GiveUserPermissions(request, ACTIVATED_USER_PERMISSIONS)
    return result


@non_cached_view(html_renderer=activate_modal_html, mobile_renderer=activate_modal_mobile,
                 methods=['GET'])
def activate_modal(request, token):
    user = user_controller.GetUserByToken(token, False, False)
    result = ResponseResult()
    if user is None:
        result.errors.append(RESPONSE_RESULT_ERROR_REDIRECT)
        result.data['next'] = '/'
        return result
    t = ConfirmToken.getToken(token, False, False)

    if t:
        type = t.Type
    else:
        result.errors.append(RESPONSE_RESULT_ERROR_404)
        return result

    if user_controller.GetProfile(user):
        user_controller.login_without_password(request, user)
        request.session['user_renew_location'] = True
    return result


@non_cached_view(json_renderer=lambda request, result, *args: activate_renderer_json(request, result),
                 methods=['GET', 'POST'],
                 validator=lambda request, *args, **kwargs: form_validator(request,
                                                                           request.user.Profile.isSSS and ExtenedSignUpSSS or ExtenedSignUp,
                                                                           initial=request.user.Profile.isSSS and {
                                                                               'mobile': request.user.Profile.Mobile,
                                                                               'username': request.user.username
                                                                           } or {'email': request.user.email}),
                 login_required=True, post_login_required=True)
def activate_user(request):
    result = ResponseResult()
    token = request.COOKIES.get('a_t_' + str(request.user.username), None)
    if token is None:
        result.errors.append(RESPONSE_RESULT_ERROR_REDIRECT)
        return result

    user = user_controller.GetUserByToken(token, True, False)
    if user is None or request.user != user:
        result.errors.append(RESPONSE_RESULT_ERROR_REDIRECT)
        result.data['next'] = '/'
        return result

    if user.is_active:
        result.messages.append(('error', _("You are already active")))
        result.errors.append(RESPONSE_RESULT_ERROR_REDIRECT)
        return result

    t = ConfirmToken.getToken(token, True, False)

    if not t:
        result.errors.append(RESPONSE_RESULT_ERROR_REDIRECT)
        return result

    type = t.Type
    source_email = None
    if t.Email and t.Email.strip() != '':
        source_email = t.Email

    if request.method == 'POST':
        if user.Profile.isSSS:
            form = ExtenedSignUpSSS(request.POST, request.FILES, initial={'username': user.username})
            if not form.is_valid():
                result.errors.append(RESPONSE_RESULT_ERROR_BAD_REQUEST)
                result.form_errors = form.errors
                return result
            user_controller.CompleteSignUpSSS(request, form.cleaned_data['firstname'], form.cleaned_data['lastname'],
                                              form.cleaned_data['password'], user, form.cleaned_data['username'], token, type,
                                              form.cleaned_data['email'], bool(int(form.cleaned_data['sex'])),
                                              form.cleaned_data['birthdate'])
            result.data['next'] = '/user/' + form.cleaned_data['username'] + '/'
        else:
            form = ExtenedSignUp(request.POST, request.FILES, initial={'email': user.email})
            if not form.is_valid():
                result.errors.append(RESPONSE_RESULT_ERROR_BAD_REQUEST)
                result.form_errors = form.errors
                return result
            email = form.cleaned_data['email']
            if source_email is not None:
                email = source_email
            user_controller.CompleteSignUp(request, user, token, type, form.cleaned_data['username'], email,
                                           form.cleaned_data['mobile'], bool(int(form.cleaned_data['sex'])), form.cleaned_data['birthdate'])
            user_controller.GiveUserPermissions(request, ACTIVATED_USER_PERMISSIONS)
    else:
        if request.user.Profile.isSSS:
            init = {'tokentype': type, 'mobile': request.user.Profile.Mobile, 'username': request.user.username}
            if source_email:
                init['email'] = source_email
            form = ExtenedSignUpSSS(initial=init)
            result.data['form'] = form
        else:
            email = request.user.email
            if source_email:
                email = source_email
            init = {'username': request.user.username, 'tokentype': type}
            if type == constants.TOKEN_TYPE_HTML_EMAIL:
                init['email'] = email
            elif type == constants.TOKEN_TYPE_HTML_NUM:
                init['mobile'] = request.user.Profile.Mobile
            form = ExtenedSignUp(initial=init)
    result.data['form'] = form
    return result


@non_cached_view(api_renderer=operation_api,
                 methods=['POST'],
                 validator=lambda request, *args, **kwargs: form_validator(request, APISignUpForm))
@refresh_cache(tags=[CACHE_TAG_USERS])
def api_signup(request):
    form = APISignUpForm(request.POST, request.FILES)
    form.is_valid()
    user = user_controller.SignUpUserFromAPI(request, form.cleaned_data['username'], form.cleaned_data['email'],
                                             form.cleaned_data['password'])
    result = ResponseResult()
    result.messages.append(('success', _('Congratulations! You are now a member of the Shout community.')))
    user_controller.GiveUserPermissions(None, INITIAL_USER_PERMISSIONS, user)
    return result


@csrf_exempt
@non_cached_view(methods=['POST'], api_renderer=user_api, json_renderer=signin_renderer_json)
@refresh_cache(tags=[CACHE_TAG_USERS])
def fb_auth(request):
    result = ResponseResult()

    if request.method == "POST":
        auth_response = json.loads(request.POST['data'])
        user = facebook_controller.user_from_facebook_auth_response(request, auth_response)
        if user:
            result.data['profile'] = user.Profile
            result.data['is_following'] = False
            result.data['owner'] = True
            result.data['username'] = user.username
            result.messages.append(('success', _('Your Facebook account has been added to Shoutit!')))
        else:
            result.messages.append(('error', _('Error connecting to your Facebook account')))
            result.errors.append(RESPONSE_RESULT_ERROR_BAD_REQUEST)
    return result


@csrf_exempt
@non_cached_view(methods=['POST'], api_renderer=user_api, json_renderer=signin_renderer_json)
@refresh_cache(tags=[CACHE_REFRESH_LEVEL_ALL])
def gplus_auth(request):
    result = ResponseResult()

    if request.method == "POST":
        try:
            post_data = json.loads(request.body)
            code = post_data['code']
        except ValueError:
            result.messages.append(('error', _('Invalid json')))
            result.errors.append(RESPONSE_RESULT_ERROR_BAD_REQUEST)
            return result
        except KeyError, e:
            result.messages.append(('error', _('Missing parameter: ' + e.message)))
            result.errors.append(RESPONSE_RESULT_ERROR_BAD_REQUEST)
            return result

        try:
            error, user = user_from_gplus_code(request, code)
        except KeyError, e:
            result.messages.append(('error', _('Invalid client: ' + unicode(e.message))))
            result.errors.append(RESPONSE_RESULT_ERROR_BAD_REQUEST)
            return result
        except BaseException, e:
            result.messages.append(('error', _(e.message)))
            result.errors.append(RESPONSE_RESULT_ERROR_BAD_REQUEST)
            return result

        if user:
            result.data['profile'] = user.Profile
            result.data['is_following'] = False
            result.data['owner'] = True
            result.data['username'] = user.username
            result.messages.append(('success', _('Your Google account has been added to Shoutit!')))
        else:
            result.messages.append(('error', _('Error connecting to your Google account')))
            result.messages.append(('error', error.message))
            result.errors.append(RESPONSE_RESULT_ERROR_BAD_REQUEST)

    return result


@non_cached_view(
    methods=['POST'],
    validator=lambda request, *args, **kwargs: form_validator(request, RecoverForm, _('Username or email you entered does not exist.')),
    json_renderer=lambda request, result, *args, **kwargs:
    json_renderer(request, result, _('We sent you an email with instructions to recover your account.'))
)
def recover(request):
    result = ResponseResult()
    form = RecoverForm(request.POST)
    form.is_valid()
    username_or_email = form.cleaned_data['username_or_email']
    profile = user_controller.GetUserByEmail(username_or_email)
    if not profile:
        profile = user_controller.GetUser(username_or_email)
        if profile is None:
            result.errors.append(RESPONSE_RESULT_ERROR_BAD_REQUEST)
            return result
    user = profile.User
    email = user.email
    token = user_controller.SetRecoveryToken(user)
    email_controller.SendPasswordRecoveryEmail(user, email,
                                               "http://%s%s" % (settings.SHOUT_IT_DOMAIN, '/' + token + '/'))
    return result


@non_cached_view(methods=['GET', 'POST'], json_renderer=resend_activation_json,
                 validator=lambda request, *args, **kwargs: form_validator(request, ReActivate),
)
def resend_activation(request):
    result = ResponseResult()
    if request.user.is_active:
        result.messages.append(('error', _("You are already active")))
        result.errors.append(RESPONSE_RESULT_ERROR_REDIRECT)
        return result
    if request.method == "POST":
        form = ReActivate(request.POST, request.FILES)
        form.is_valid()
        user_controller.ChangeEmailAndSendActivation(request, request.user, form.cleaned_data['email'])
    else:
        init = {'email': request.user.email, 'username': request.user.username}
        form = ReActivate(initial=init)
        result.data['form'] = form
    return result


@non_cached_view(methods=['GET', 'POST'], login_required=True, api_renderer=operation_api,
                 json_renderer=lambda request, result, username:
                 json_renderer(request, result, _('You are now listening to %(name)s\'s shouts.') % {
                     'name': user_controller.GetUser(username).name() if user_controller.GetUser(username) else ''}),
                 validator=lambda request, username: object_exists_validator(user_controller.GetUser,
                                                                             _('User %(username)s does not exist.') %
                                                                             {'username': username}, username),
                 permissions_required=[PERMISSION_ACTIVATED, PERMISSION_FOLLOW_USER])
@refresh_cache(level=CACHE_LEVEL_GLOBAL, tags=[CACHE_TAG_STREAMS, CACHE_TAG_USERS, CACHE_TAG_NOTIFICATIONS])
def follow_user(request, username):
    user_controller.FollowStream(request, request.user.username, user_controller.GetUser(username).Stream)
    realtime_controller.BindUserToUser(request.user.username, username)
    #refresh_cache_dynamically([CACHE_TAG_STREAMS.make_dynamic(request.user)])
    return ResponseResult()


@non_cached_view(methods=['GET', 'DELETE'],
                 login_required=True,
                 api_renderer=operation_api,
                 json_renderer=lambda request, result, username: json_renderer(request,
                                                                               result,
                                                                               _('You are no longer listening to %(name)s\'s shouts.') % {
                                                                                   'name': user_controller.GetUser(
                                                                                       username).name() if user_controller.GetUser(
                                                                                       username) else ''},
                                                                               success_message_type='info'),
                 validator=lambda request, username: object_exists_validator(user_controller.GetUser,
                                                                             _('User %(username)s does not exist.') % {
                                                                             'username': username}, username))
@refresh_cache(level=CACHE_LEVEL_USER, tags=[CACHE_TAG_STREAMS, CACHE_TAG_USERS])
def unfollow_user(request, username):
    user_controller.UnfollowStream(request, request.user.username, user_controller.GetUser(username).Stream)
    realtime_controller.UnbindUserFromUser(request.user.username, username)
    #refresh_cache_dynamically([CACHE_TAG_STREAMS.make_dynamic(request.user)])
    return ResponseResult()


@non_cached_view(
    json_renderer=lambda request, result, *args, **kwrgs: profile_json_renderer(request, result),
    api_renderer=profiles_api,
    methods=['GET'])
def search_user(request, keyword):
    limit = 6

    flag = int(USER_TYPE_INDIVIDUAL | USER_TYPE_BUSINESS)
    email_search = False

    if request.GET.has_key('type'):
        flag = int(request.GET['type'])
    if request.GET.has_key('email_search'):
        email_search = request.GET['email_search']

    try:
        email_search = int(email_search) and True or False
    except ValueError, e:
        email_search = False

    users = list(user_controller.SearchUsers(keyword, flag, 0, limit, email_search))
    result = ResponseResult()
    result.data['users'] = users
    return result


@csrf_exempt
@non_cached_view(methods=['GET', 'POST'], json_renderer=json_data_renderer, api_renderer=operation_api)
# @refresh_cache(level=CACHE_REFRESH_LEVEL_SESSION, tags=[CACHE_TAG_STREAMS, CACHE_TAG_TAGS])
#TODO: is it important the refresh cache decorator?
def set_user_session_location_info(request):
    result = ResponseResult()
    request.session['user_lat'] = float(request.REQUEST['user_lat'])
    request.session['user_lng'] = float(request.REQUEST['user_lng'])
    request.session['user_country'] = request.REQUEST['user_country']
    request.session['user_city'] = request.REQUEST['user_city']
    return result


@non_cached_view(html_renderer=lambda request, result: page_html(request, result, 'signin.html', 'Sign In'),
                 json_renderer=signin_renderer_json,
                 methods=['GET', 'POST'],
                 validator=lambda request, *args, **kwargs: form_validator(request, LoginForm, _('Invalid credentials.')))
def signin(request):
    result = ResponseResult()
    if request.method == 'POST':
        form = LoginForm(request.POST)
        form.is_valid()
        user = user_controller.SignInUser(request, form.cleaned_data['password'],
                                          form.cleaned_data['username_or_email'])
        result.data['username'] = user.username
        if request.POST.has_key('next'):
            result.data['next'] = request.POST['next']
        else:
            result.data['next'] = '/'

        if request.session.has_key('business_user_id'):
            result.data['next'] = '/bsignup/'

    else:
        form = LoginForm()
        if request.GET.has_key('next'):
            next = request.GET['next']
        else:
            next = '/'
        result.data['next'] = next
    result.data['form'] = form
    return result


@non_cached_view(html_renderer=lambda request, result: page_html(request, result, 'signup.html', 'Sign Up'),
                 json_renderer=lambda request, result: json_renderer(request,
                                                                     result,
                                                                     success_message=_(
                                                                         'Congratulations! You are now a member of the Shout community.')),
                 api_renderer=operation_api,
                 methods=['GET', 'POST'],
                 validator=lambda request, *args, **kwargs: form_validator(request, SignUpForm))
@refresh_cache(tags=[CACHE_TAG_STREAMS])
def signup(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        form.is_valid()
        user = user_controller.SignUpUser(request, form.cleaned_data['firstname'], form.cleaned_data['lastname'],
                                          form.cleaned_data['password'], form.cleaned_data['email'])
        user_controller.GiveUserPermissions(None, INITIAL_USER_PERMISSIONS, user)
    else:
        form = SignUpForm()
    result = ResponseResult()
    result.data['form'] = form
    return result


@non_cached_view(html_renderer=lambda request, result: HttpResponseRedirect('/'),
                 json_renderer=lambda request, result: json_renderer(request,
                                                                     result,
                                                                     success_message=_('You are now signed out.'),
                                                                     data={'next': '/'}),
                 methods=['GET'])
def signout(request):
    if request.user.is_authenticated():
        user_controller.SignOut(request)
    return ResponseResult()


def sss(request):
    if request.method == "POST":
        shout = json.loads(request.POST['json'])
        try:
            user = user_controller.GetUserByMobile(shout['mobile']) or None

            if user is None:
                user = user_controller.SignUpSSS(None, mobile=shout['mobile'], location=shout['location'],
                                                 country=shout['country'], city=shout['city'])
                user_controller.GiveUserPermissions(None, INITIAL_USER_PERMISSIONS, user)
            else:
                user = user.User
        except BaseException, e:
            return HttpResponseBadRequest("User Creation Error: " + str(e))

        try:
            shout['price'] = shout['price'] if shout['price'] else 1
            for tag in shout['tags']:
                if tag:
                    if tag.find('Ref-') != -1 or tag.find('SqFt') != -1:
                        shout['tags'].remove(tag)

            if shout['type'] == 'buy':
                shout = shout_controller.shout_buy(
                    None, name=shout['name'], text=shout['text'], price=shout['price'], currency=shout['currency'],
                    latitude=float(shout['location'][0]),
                    longitude=float(shout['location'][1]), tags=shout['tags'], shouter=user,
                    country_code=shout['country'],
                    province_code=shout['city'], address='', images=shout['images'], issss=True,
                    exp_days=settings.MAX_EXPIRY_DAYS_SSS
                )
            else:
                shout = shout_controller.shout_sell(
                    None, name=shout['name'], text=shout['text'], price=shout['price'], currency=shout['currency'],
                    latitude=float(shout['location'][0]),
                    longitude=float(shout['location'][1]), tags=shout['tags'], shouter=user_controller.GetUser(user.username),
                    country_code=shout['country'],
                    province_code=shout['city'], address='', images=shout['images'], issss=True,
                    exp_days=settings.MAX_EXPIRY_DAYS_SSS
                )

        except BaseException, e:
            return HttpResponseBadRequest("Shout Creation Error: " + str(e))

        return HttpResponse('Done')


@non_cached_view(methods=['GET'],
                 json_renderer=json_data_renderer)
#@refresh_cache(level=CACHE_REFRESH_LEVEL_USER, tags=[CACHE_TAG_USERS, CACHE_TAG_STREAMS, CACHE_TAG_TAGS])
def update_user_location(request):
    result = ResponseResult()

    latlong = request.GET[u'latlong']
    latitude = float(latlong.split(',')[0].strip())
    longitude = float(latlong.split(',')[1].strip())

    userProfile = user_controller.GetProfile(request.user)
    old_city = userProfile.City
    new_city = request.GET[u'city']

    userProfile = user_controller.UpdateLocation(request.user.username, latitude, longitude, new_city,
                                                 request.GET[u'country'])
    result.data['user_lat'] = request.session['user_lat'] = userProfile.Latitude
    result.data['user_lng'] = request.session['user_lng'] = userProfile.Longitude
    result.data['user_country'] = request.session['user_country'] = userProfile.Country
    result.data['user_city'] = request.session['user_city'] = userProfile.City
    result.data['user_city_encoded'] = request.session['user_city_encoded'] = ToSeoFriendly(unicode.lower(unicode(userProfile.City)))

    if new_city and new_city != old_city:
        realtime_controller.UnbindUserFromCity(request.user.username, old_city)
        realtime_controller.BindUserToCity(request.user.username, new_city)

    return result


@non_cached_view(
    json_renderer=edit_profile_renderer_json,
    login_required=True,
    validator=lambda request, username: user_edit_profile_validator(request, username, user_controller.GetUser(username).User.email),
    permissions_required=[PERMISSION_ACTIVATED])
@refresh_cache(tags=[CACHE_TAG_USERS])
def user_edit_profile(request, username):
    user_profile = user_controller.GetUser(username)
    result = ResponseResult()
    result.data['user_profile'] = user_profile
    if request.method == 'POST':
        form = UserEditProfileForm(request.POST, request.FILES,
                                   initial={'username': username, 'email': user_profile.User.email})
        form.is_valid()

        if form.cleaned_data.has_key('username') and form.cleaned_data['username']:
            user_profile.User.username = form.cleaned_data['username']
            result.data['next'] = '/user/' + form.cleaned_data['username']
        if form.cleaned_data.has_key('email') and form.cleaned_data['email']:
            user_profile.User.email = form.cleaned_data['email']
        if form.cleaned_data.has_key('firstname') and form.cleaned_data['firstname']:
            user_profile.User.first_name = form.cleaned_data['firstname']
        if form.cleaned_data.has_key('lastname') and form.cleaned_data['lastname']:
            user_profile.User.last_name = form.cleaned_data['lastname']
        if form.cleaned_data.has_key('mobile') and form.cleaned_data['mobile']:
            user_profile.Mobile = form.cleaned_data['mobile']

        user_profile.Birthdate = form.cleaned_data['birthdate']
        user_profile.Sex = bool(int(form.cleaned_data['sex']))
        if user_profile.Image.endswith('user_female.png') or user_profile.Image.endswith('user_male.png'):
            user_profile.Image = '/static/img/_user_' + (
                user_profile.Sex and 'male.png' or 'female.png')

        user_profile.Bio = form.cleaned_data['bio']
        if form.cleaned_data.has_key('password') and form.cleaned_data['password']:
            user_profile.User.set_password(form.cleaned_data['password'])

        user_profile.User.save()
        user_profile.save()
        result.messages.append(('success', _('Your profile was updated successfully.')))
    else:
        form = UserEditProfileForm(
            initial={'email': user_profile.email, 'bio': user_profile.Bio, 'username': user_profile.username,
                     'firstname': user_profile.User.first_name, 'lastname': user_profile.User.last_name,
                     'mobile': user_profile.Mobile, 'sex': int(user_profile.Sex), 'birthdate': user_profile.Birthdate})
    result.data['form'] = form
    return result


@cached_view(level=CACHE_LEVEL_USER,
             tags=[CACHE_TAG_STREAMS, CACHE_TAG_USERS],
             methods=['GET'],
             api_renderer=shouts_api,
             json_renderer=lambda request, result, username, *args: user_stream_json(request, result),
             html_renderer=lambda request, result, username, *args: object_page_html(request, result, 'user_profile.html',
                                                                                     result.data.has_key('user_profile') and result.data[
                                                                                         'user_profile'].username or ''),
             validator=user_profile_validator)
def user_stream(request, username, page_num=None):
    if username == '@me':
        username = request.user.username

    if not page_num:
        page_num = 1
    else:
        page_num = int(page_num)
    result = ResponseResult()
    user_profile = user_controller.GetUser(username)
    result.data['shouts_count'] = user_profile.Stream.Posts.filter(Q(Type=POST_TYPE_BUY) | Q(Type=POST_TYPE_SELL)).count()
    result.data['pages_count'] = int(math.ceil(result.data['shouts_count'] / float(DEFAULT_PAGE_SIZE)))
    #result.data['shouts'] = get_data([CACHE_TAG_STREAMS.make_dynamic(user_profile.Stream)], stream_controller.GetStreamShouts, user_profile.Stream, DEFAULT_PAGE_SIZE * (page_num - 1), DEFAULT_PAGE_SIZE * page_num)
    result.data['shouts'] = stream_controller.GetStreamShouts(user_profile.Stream, DEFAULT_PAGE_SIZE * (page_num - 1),
                                                              DEFAULT_PAGE_SIZE * page_num)
    result.data['is_last_page'] = page_num == result.data['pages_count']
    return result


@cached_view(level=CACHE_LEVEL_USER,
             tags=[CACHE_TAG_STREAMS, CACHE_TAG_USERS],
             methods=['GET'],
             api_renderer=user_api,
             html_renderer=lambda request, result, username, *args:
             object_page_html(request, result, isinstance(user_controller.GetUser(username), UserProfile) and 'user_profile.html' or 'business_profile.html',
                              'profile' in result.data and result.data['profile'].name() or '',
                              'profile' in result.data and result.data['profile'].Bio or ''),
             validator=user_profile_validator)
def user_profile(request, username):
    if username == '@me':
        username = request.user.username

    profile = user_controller.GetUser(username)

    result = ResponseResult()
    result.data['profile'] = profile
    result.data['owner'] = request.user.is_authenticated() and request.user.pk == profile.User.pk
    result.data['shouts'] = stream_controller.GetStreamShouts(profile.Stream, 0, DEFAULT_PAGE_SIZE,
                                                              result.data['owner'])

    #	result.data['shouts_count'] = profile.User.Posts.GetValidShouts(types=[POST_TYPE_BUY,POST_TYPE_SELL]).count()
    result.data['offers_count'] = Trade.objects.GetValidTrades(types=[POST_TYPE_SELL]).filter(OwnerUser=profile.User).count()
    result.data['followers_count'] = profile.Stream.userprofile_set.count()
    result.data['is_following'] = (request.user.is_authenticated() and len(
        FollowShip.objects.filter(follower__User__pk=request.user.pk, stream__id=profile.Stream_id)) > 0) or False

    if isinstance(profile, UserProfile):
        result.data['following_count'] = profile.Following.count()
        result.data['interests'] = user_controller.UserFollowing(username, 'tags', 'recent')['tags']
        result.data['interests_count'] = len(user_controller.UserFollowing(username, 'tags', 'all')['tags'])
        result.data['requests_count'] = Trade.objects.GetValidTrades(types=[POST_TYPE_BUY]).filter(OwnerUser=profile.User).count()
        result.data['experiences_count'] = experience_controller.GetExperiencesCount(profile)
        fb_la = LinkedFacebookAccount.objects.filter(User=profile.User).order_by('-pk')[:1]
        result.data['user_profile_fb'] = fb_la[0].link if fb_la else None
        result.data['fb_og_type'] = 'user'

    if isinstance(profile, BusinessProfile):
        thumps_count = experience_controller.GetBusinessThumbsCount(profile)
        result.data['thumb_up_count'] = thumps_count['ups']
        result.data['thumb_down_count'] = thumps_count['downs']
        result.data['recent_experiences'] = experience_controller.GetExperiences(user=request.user, about_business=profile, start_index=0,
                                                                                 end_index=5)
        #		result.data['recent_items'] = gallery_controller.GetBusinessGalleryItems(profile,0,5)
        if request.user == profile.User:
            result.data['item_form'] = ItemForm()
            result.data['IsOwner'] = 1
        else:
            result.data['IsOwner'] = 0
        result.data['fb_og_type'] = 'business'

    result.data['report_form'] = ReportForm()
    result.data['is_fb_og'] = True
    result.data['fb_og_url'] = 'http%s://%s/user/%s/' % ('s' if settings.IS_SITE_SECURE else '', settings.SHOUT_IT_DOMAIN,
                                                         profile.User.username)
    return result


@cached_view(level=CACHE_LEVEL_USER,
             tags=[CACHE_TAG_STREAMS, CACHE_TAG_USERS],
             methods=['GET'],
             api_renderer=user_api,
             validator=user_profile_validator)
def user_profile_brief(request, username):
    if username == '@me':
        username = request.user.username
    user_profile = user_controller.GetUser(username)
    result = ResponseResult()

    #	result.data['shouts_count'] = user_profile.User.Posts.GetValidShouts(types=[POST_TYPE_BUY,POST_TYPE_SELL]).count()
    result.data['shouts_count'] = Trade.objects.GetValidTrades().filter(OwnerUser=user_profile.User).count()

    result.data['followers_count'] = user_profile.Stream.userprofile_set.count()
    result.data['following_count'] = user_profile.Following.count()
    result.data['interests_count'] = len(user_controller.UserFollowing(username, 'tags', 'all')['tags'])
    result.data['tags_created_count'] = user_profile.TagsCreated.count()
    result.data['profile'] = user_profile
    result.data['owner'] = request.user.is_authenticated() and request.user.pk == user_profile.User.pk
    result.data['is_following'] = (request.user.is_authenticated() and len(
        FollowShip.objects.filter(follower__User__pk=request.user.pk, stream__id=user_profile.Stream_id)) > 0) or False
    return result


@cached_view(level=CACHE_LEVEL_GLOBAL,
             tags=[CACHE_TAG_STREAMS, CACHE_TAG_USERS, CACHE_TAG_TAGS],
             methods=['GET'],
             json_renderer=json_data_renderer,
             api_renderer=stats_api,
             validator=user_profile_validator)
def user_stats(request, username, statsType, followingType, period='recent'):
    if username == '@me':
        username = request.user.username
    result = ResponseResult()
    if statsType == 'followers':
        followers = user_controller.UserFollowers(username)
        if hasattr(request, 'is_api') and request.is_api:
            result.data['followers'] = followers
        else:
            from apps.shoutit.templatetags import template_filters

            result.data['followers'] = [
                {'username': user.username, 'name': user.name(), 'image': template_filters.thumbnail(user.Image, 32)}
                for user in followers]

    if statsType == 'following':
        following = user_controller.UserFollowing(username, followingType, period)
        result.data['followingTags'] = following['tags']

        if hasattr(request, 'is_api') and request.is_api:
            result.data['followingUsers'] = following['users']
        else:
            from apps.shoutit.templatetags import template_filters

            result.data['followingUsers'] = [
                {'username': u.username, 'name': u.name(), 'image': template_filters.thumbnail(u.Image, 32)} for u in
                following[
                    'users']]
    return result


@cached_view(level=CACHE_LEVEL_GLOBAL,
             tags=[CACHE_TAG_USERS],
             json_renderer=json_data_renderer,
             methods=['GET'])
def top_users(request):
    result = ResponseResult()
    if not request.session.has_key('user_country'):
        result.data['top_users'] = []
        return result

    user_country = request.session['user_country']
    user_city = request.session['user_city']

    result.data['top_users'] = user_controller.GetTopUsers(7, user_country, user_city)
    if request.user.is_authenticated():
        user_following = user_controller.UserFollowing(request.user.username, 'users', 'all')['users']
        user_following = UserProfile.objects.values('User__username').filter(pk__in=[u.pk for u in user_following])
        for top_user in result.data['top_users']:
            top_user['is_following'] = {'User__username': top_user['User__username']} in user_following
            top_user['is_you'] = top_user['User__username'] == request.user.username
    else:
        for top_user in result.data['top_users']:
            top_user['is_following'] = False
    return result


@csrf_exempt
@login_required
@non_cached_view(html_renderer=lambda request, result, *args, **kwargs: page_html(request, result, 'contact_list.html',
                                                                                  _('Invite your contacts to Shoutit.')))
def import_contacts(request, contact_provider):
    result = ResponseResult()
    contacts = contact_provider.get_contact_list()
    contacts.sort(key=lambda x: x['name'].lower())
    result.data['contacts'] = contacts
    return result


@non_cached_view(
    json_renderer=lambda request, result: json_renderer(request, result, _('Thank you, we will send your friends your invitation.')))
def send_invitations(request):
    result = ResponseResult()
    emails = []
    if request.POST.has_key('emails'):
        emails = request.POST.getlist('emails')
    elif request.POST.has_key('emails[]'):
        emails = request.POST.getlist('emails[]')

    if emails:
        names_emails_dict = {email.split('|')[0]: email.split('|')[1] for email in emails}
        email_controller.SendInvitationEmail(request.user, names_emails_dict)

    return result


@non_cached_view(methods=['GET'],
                 api_renderer=activities_api,
                 json_renderer=lambda request, result, *args: activities_stream_json(request, result))
def activities_stream(request, username, page_num=None):
    if username == '@me':
        username = request.user.username

    if not page_num:
        page_num = 1
    else:
        page_num = int(page_num)
    result = ResponseResult()
    user = user_controller.GetUser(username)

    start_index = DEFAULT_PAGE_SIZE * (page_num - 1)
    end_index = DEFAULT_PAGE_SIZE * page_num

    post_count, stream_posts = user_controller.activities_stream(user, start_index, end_index)
    result.data['pages_count'] = int(math.ceil(post_count / float(DEFAULT_PAGE_SIZE)))
    result.data['is_last_page'] = page_num >= result.data['pages_count']
    result.data['posts'] = stream_posts
    return result
