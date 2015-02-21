import math
import json
import urllib2

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseRedirect
from django.views.decorators.csrf import csrf_exempt
from django.utils.translation import ugettext_lazy as _
from django.conf import settings
from push_notifications.models import GCMDevice, APNSDevice

from shoutit.models import ConfirmToken, Business, Profile, Trade, Video
from shoutit.controllers.facebook_controller import user_from_facebook_auth_response
from shoutit.controllers.gplus_controller import user_from_gplus_code
from shoutit.forms import ExtenedSignUpSSS, APISignUpForm, ReActivate, SignUpForm, RecoverForm, LoginForm, ReportForm, ItemForm, \
    UserEditProfileForm, ExtenedSignUp
from shoutit.tiers import non_cached_view, ResponseResult, RESPONSE_RESULT_ERROR_BAD_REQUEST, RESPONSE_RESULT_ERROR_404
from renderers import page_html, activate_modal_html, activate_modal_mobile, object_page_html, user_location, push_user_api, \
    user_video_renderer
from renderers import user_api, operation_api, profiles_api, shouts_api, stats_api, activities_api
from renderers import activate_renderer_json, signin_renderer_json, json_renderer, json_data_renderer, profile_json_renderer, \
    resend_activation_json, edit_profile_renderer_json, user_stream_json, activities_stream_json
from renderers import RESPONSE_RESULT_ERROR_REDIRECT
from shoutit.controllers import stream_controller, realtime_controller, email_controller, user_controller, experience_controller
from validators import form_validator, object_exists_validator, user_edit_profile_validator, user_profile_validator, activate_api_validator, \
    push_validator, user_profile_edit_validator
from common.constants import TOKEN_TYPE_HTML_EMAIL, TOKEN_TYPE_HTML_NUM, TOKEN_TYPE_API_EMAIL, DEFAULT_PAGE_SIZE, POST_TYPE_REQUEST, \
    POST_TYPE_OFFER, USER_TYPE_BUSINESS, USER_TYPE_INDIVIDUAL, STREAM2_TYPE_TAG, STREAM2_TYPE_PROFILE
from shoutit.permissions import PERMISSION_ACTIVATED, PERMISSION_FOLLOW_USER, INITIAL_USER_PERMISSIONS, ACTIVATED_USER_PERMISSIONS
from shoutit.utils import to_seo_friendly, user_link
from shoutit.templatetags.template_filters import thumbnail


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
                                   form.cleaned_data['mobile'], bool(int(form.cleaned_data['sex'])), form.cleaned_data['birthday'])
    result.messages.append(('success', _('You are now activated.')))
    user_controller.give_user_permissions(request, ACTIVATED_USER_PERMISSIONS)
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
    return result


@non_cached_view(json_renderer=lambda request, result, *args: activate_renderer_json(request, result),
                 methods=['GET', 'POST'],
                 validator=lambda request, *args, **kwargs: form_validator(request,
                                                                           request.user.profile.isSSS and ExtenedSignUpSSS or ExtenedSignUp,
                                                                           initial=request.user.profile.isSSS and {
                                                                               'mobile': request.user.profile.Mobile,
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
        if user.profile.isSSS:
            form = ExtenedSignUpSSS(request.POST, request.FILES, initial={'username': user.username})
            if not form.is_valid():
                result.errors.append(RESPONSE_RESULT_ERROR_BAD_REQUEST)
                result.form_errors = form.errors
                return result
            user_controller.CompleteSignUpSSS(request, form.cleaned_data['firstname'], form.cleaned_data['lastname'],
                                              form.cleaned_data['password'], user, form.cleaned_data['username'], token, type,
                                              form.cleaned_data['email'], bool(int(form.cleaned_data['sex'])),
                                              form.cleaned_data['birthday'])
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
                                           form.cleaned_data['mobile'], bool(int(form.cleaned_data['sex'])), form.cleaned_data['birthday'])
            user_controller.give_user_permissions(request, ACTIVATED_USER_PERMISSIONS)
    else:
        if request.user.profile.isSSS:
            init = {'tokentype': type, 'mobile': request.user.profile.Mobile, 'username': request.user.username}
            if source_email:
                init['email'] = source_email
            form = ExtenedSignUpSSS(initial=init)
            result.data['form'] = form
        else:
            email = request.user.email
            if source_email:
                email = source_email
            init = {'username': request.user.username, 'tokentype': type}
            if type == TOKEN_TYPE_HTML_EMAIL:
                init['email'] = email
            elif type == TOKEN_TYPE_HTML_NUM:
                init['mobile'] = request.user.profile.Mobile
            form = ExtenedSignUp(initial=init)
    result.data['form'] = form
    return result


@non_cached_view(methods=['POST'], api_renderer=operation_api,
                 validator=lambda request, *args, **kwargs: form_validator(request, APISignUpForm))
def api_signup(request):
    form = APISignUpForm(request.POST, request.FILES)
    form.is_valid()
    user = user_controller.SignUpUserFromAPI(request, username=form.cleaned_data['username'], email=form.cleaned_data['email'],
                                             password=form.cleaned_data['password'], first_name='', last_name='', birthday=None, sex=True)
    result = ResponseResult()
    result.messages.append(('success', _('Congratulations! You are now a member of the Shout community.')))
    user_controller.give_user_permissions(None, INITIAL_USER_PERMISSIONS, user)
    return result


@csrf_exempt
@non_cached_view(methods=['POST'], api_renderer=user_api, json_renderer=signin_renderer_json)
def fb_auth(request):
    result = ResponseResult()

    fb_auth_response = request.json_data
    error, user = user_from_facebook_auth_response(request, fb_auth_response)

    if user:
        result.data['profile'] = user.profile
        result.data['is_listening'] = False
        result.data['owner'] = True
        result.data['username'] = user.username
        result.messages.append(('success', _('Your Facebook account has been added to Shoutit!')))
    else:
        result.messages.append(('error', _('Error connecting to your Facebook account')))
        result.messages.append(('error', error.message))
        result.errors.append(RESPONSE_RESULT_ERROR_BAD_REQUEST)

    return result


@csrf_exempt
@non_cached_view(methods=['POST'], api_renderer=user_api, json_renderer=signin_renderer_json)
def gplus_auth(request):
    result = ResponseResult()

    try:
        gplus_auth_response = request.json_data
        code = gplus_auth_response['code']
    except KeyError, e:
        result.messages.append(('error', _("Invalid google response")))
        result.errors.append(RESPONSE_RESULT_ERROR_BAD_REQUEST)
        return result

    error, user = user_from_gplus_code(request, code, client='shoutit-web')

    if user:
        result.data['profile'] = user.profile
        result.data['is_listening'] = False
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
        profile = user_controller.get_profile(username_or_email)
        if profile is None:
            result.errors.append(RESPONSE_RESULT_ERROR_BAD_REQUEST)
            return result
    user = profile.user
    email = user.email
    token = user_controller.SetRecoveryToken(user)
    email_controller.SendPasswordRecoveryEmail(user, email, "%s%s/" % (settings.SITE_LINK, token))
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


# todo: validator for @me and not to listen to your self
@non_cached_view(methods=['GET', 'POST'], login_required=True, api_renderer=operation_api,
                 permissions_required=[PERMISSION_ACTIVATED, PERMISSION_FOLLOW_USER],
                 json_renderer=lambda request, result, username:
                 json_renderer(request, result, _('You are now listening to %(name)s\'s shouts.') % {
                     'name': user_controller.get_profile(username).name if user_controller.get_profile(username) else ''}),
                 validator=lambda request, username: object_exists_validator(user_controller.get_profile, False,
                                                                             _('User %(username)s does not exist.') %
                                                                             {'username': username}, username))
def start_listening_to_user(request, username):
    profile = request.validation_result.data
    stream_controller.listen_to_stream(request.user, profile.stream2)
    return ResponseResult()


# todo: validator for @me and not to listen to your self
@non_cached_view(methods=['GET', 'DELETE'], login_required=True,
                 api_renderer=operation_api,
                 json_renderer=lambda request, result, username: json_renderer(request,
                                                                               result,
                                                                               _('You are no longer listening to %(name)s\'s shouts.') % {
                                                                                   'name': user_controller.get_profile(
                                                                                       username).name if user_controller.get_profile(
                                                                                       username) else ''},
                                                                               success_message_type='info'),
                 validator=lambda request, username: object_exists_validator(user_controller.get_profile, False,
                                                                             _('User %(username)s does not exist.') % {
                                                                                 'username': username}, username))
def stop_listening_to_user(request, username):
    profile = request.validation_result.data
    stream_controller.remove_listener_from_stream(request.user, profile.stream2)
    return ResponseResult()


@non_cached_view(methods=['GET'], api_renderer=profiles_api,
                 json_renderer=lambda request, result, *args, **kwargs: profile_json_renderer(request, result))
def search_user(request):
    result = ResponseResult()
    limit = 6

    query = unicode(request.GET.get('query', ''))
    flag = int(request.GET.get('type', USER_TYPE_INDIVIDUAL | USER_TYPE_BUSINESS))
    email_search = bool(request.GET.get('email_search', False))

    result.data['users'] = list(user_controller.search_users(query, flag, 0, limit, email_search))

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
        if 'next' in request.POST:
            result.data['next'] = request.POST['next']
        else:
            result.data['next'] = '/'

        if 'business_user_id' in request.session:
            result.data['next'] = '/bsignup/'

    else:
        form = LoginForm()
        if 'next' in request.GET:
            next = request.GET['next']
        else:
            next = '/'
        result.data['next'] = next
    result.data['form'] = form
    return result


@non_cached_view(methods=['GET', 'POST'], validator=lambda request, *args, **kwargs: form_validator(request, SignUpForm),
                 html_renderer=lambda request, result: page_html(request, result, 'signup.html', 'Sign Up'),
                 json_renderer=lambda request, result: json_renderer(request,
                                                                     result,
                                                                     success_message=_(
                                                                         'Congratulations! You are now a member of the Shout community.')),
                 api_renderer=operation_api)
def signup(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        form.is_valid()
        user = user_controller.SignUpUser(request, form.cleaned_data['firstname'], form.cleaned_data['lastname'],
                                          form.cleaned_data['password'], form.cleaned_data['email'])
        user_controller.give_user_permissions(None, INITIAL_USER_PERMISSIONS, user)
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
    from shoutit.controllers import shout_controller

    if request.method == "POST":
        shout = json.loads(request.POST['json'])
        try:
            user = user_controller.GetUserByMobile(shout['mobile']) or None

            if user is None:
                user = user_controller.SignUpSSS(None, mobile=shout['mobile'], location=shout['location'],
                                                 country=shout['country'], city=shout['city'])
                user_controller.give_user_permissions(None, INITIAL_USER_PERMISSIONS, user)
            else:
                user = user.user
        except Exception, e:
            return HttpResponseBadRequest("User Creation Error: " + str(e))

        try:
            shout['price'] = shout['price'] if shout['price'] else 1
            for tag in shout['tags']:
                if tag:
                    if tag.find('Ref-') != -1 or tag.find('SqFt') != -1:
                        shout['tags'].remove(tag)

            if shout['type'] == 'buy':
                shout = shout_controller.post_request(
                    name=shout['name'], text=shout['text'], price=shout['price'], currency=shout['currency'],
                    latitude=float(shout['location'][0]),
                    longitude=float(shout['location'][1]), tags=shout['tags'], shouter=user,
                    country=shout['country'],
                    city=shout['city'], address='', images=shout['images'], is_sss=True,
                    exp_days=settings.MAX_EXPIRY_DAYS_SSS
                )
            else:
                shout = shout_controller.post_offer(
                    name=shout['name'], text=shout['text'], price=shout['price'], currency=shout['currency'],
                    latitude=float(shout['location'][0]),
                    longitude=float(shout['location'][1]), tags=shout['tags'], shouter=user_controller.get_profile(user.username),
                    country=shout['country'],
                    city=shout['city'], address='', images=shout['images'], is_sss=True,
                    exp_days=settings.MAX_EXPIRY_DAYS_SSS
                )

        except Exception, e:
            return HttpResponseBadRequest("Shout Creation Error: " + str(e))

        return HttpResponse('Done')


@csrf_exempt
@non_cached_view(methods=['PUT'], login_required=True, json_renderer=json_data_renderer, api_renderer=user_location)
def update_user_location(request):
    result = ResponseResult()
    profile = request.user.profile

    city = request.POST.get('city', None)
    country = request.POST.get('country', None)
    latitude = request.POST.get('latitude', None)
    longitude = request.POST.get('longitude', None)

    if not (city and country and latitude and longitude):
        result.messages.append(('error', _("Location should contain 'country', 'city', 'latitude', 'longitude'")))
        result.errors.append(RESPONSE_RESULT_ERROR_BAD_REQUEST)
        return result

    old_city = profile.City
    location = {
        'country': country,
        'city': city,
        'latitude': latitude,
        'longitude': longitude
    }

    profile = user_controller.update_profile_location(profile, location)
    result.data['user_lat'] = profile.Latitude
    result.data['user_lng'] = profile.Longitude
    result.data['user_country'] = profile.Country
    result.data['user_city'] = profile.City
    result.data['user_city_encoded'] = to_seo_friendly(unicode.lower(unicode(profile.City)))

    if city != old_city:
        realtime_controller.UnbindUserFromCity(request.user.username, old_city)
        realtime_controller.BindUserToCity(request.user.username, city)

    return result


@csrf_exempt
@non_cached_view(methods=['GET', 'POST', 'DELETE'], login_required=True,
                 json_renderer=json_data_renderer, api_renderer=user_video_renderer,
                 validator=user_profile_validator)
def user_video(request, username):
    result = ResponseResult()
    profile = request.validation_result.data['profile']

    if request.method == 'POST':
        v = request.json_data

        video = Video(url=v['url'], thumbnail_url=v['thumbnail_url'], provider=v['provider'], id_on_provider=v['id_on_provider'],
                      duration=v['duration'])
        video.save()
        if profile.video:
            profile.video.delete()
        profile.video = video
        profile.save()

    if request.method == 'DELETE':
        if profile.video:
            profile.video.delete()

    result.data['video'] = profile.video
    return result


@csrf_exempt
@non_cached_view(methods=['PUT'], login_required=True, validator=user_profile_edit_validator, api_renderer=user_api)
def edit_profile(request, username):
    result = ResponseResult()
    profile = request.validation_result.data['profile']
    new_attributes = request.validation_result.data['new_attributes']
    updated_profile = user_controller.update_profile_attributes(profile, new_attributes)
    result.data['profile'] = updated_profile

    return result


@non_cached_view(login_required=True, permissions_required=[PERMISSION_ACTIVATED],
                 json_renderer=edit_profile_renderer_json,

                 validator=lambda request, username: user_edit_profile_validator(request, username,
                                                                                 user_controller.get_profile(username).user.email))
def user_edit_profile(request, username):
    result = ResponseResult()
    profile = user_controller.get_profile(username)

    result.data['user_profile'] = profile
    if request.method == 'POST':
        form = UserEditProfileForm(request.POST, request.FILES, initial={'username': username, 'email': profile.user.email})
        form.is_valid()

        if 'username' in form.cleaned_data and form.cleaned_data['username']:
            profile.user.username = form.cleaned_data['username']
            result.data['next'] = '/user/' + form.cleaned_data['username'] + '/'

        if 'email' in form.cleaned_data and form.cleaned_data['email']:
            profile.user.email = form.cleaned_data['email']

        if 'firstname' in form.cleaned_data and form.cleaned_data['firstname']:
            profile.user.first_name = form.cleaned_data['firstname']

        if 'lastname' in form.cleaned_data and form.cleaned_data['lastname']:
            profile.user.last_name = form.cleaned_data['lastname']

        if 'mobile' in form.cleaned_data and form.cleaned_data['mobile']:
            profile.Mobile = form.cleaned_data['mobile']

        profile.birthday = form.cleaned_data['birthday']
        profile.Sex = bool(int(form.cleaned_data['sex']))
        if profile.image.endswith('user_female.png') or profile.image.endswith('user_male.png'):
            profile.image = '/static/img/_user_' + (
                profile.Sex and 'male.png' or 'female.png')

        profile.Bio = form.cleaned_data['bio']

        if 'password' in form.cleaned_data and form.cleaned_data['password']:
            profile.user.set_password(form.cleaned_data['password'])

        profile.user.save()
        profile.save()
        result.messages.append(('success', _('Your profile was updated successfully.')))
    else:
        form = UserEditProfileForm(
            initial={'email': profile.email, 'bio': profile.Bio, 'username': profile.username,
                     'firstname': profile.user.first_name, 'lastname': profile.user.last_name,
                     'mobile': profile.Mobile, 'sex': int(profile.Sex), 'birthday': profile.birthday})
    result.data['form'] = form
    return result


@non_cached_view(methods=['GET'], api_renderer=user_api, validator=user_profile_validator,
                 html_renderer=lambda request, result, username, *args:
                 object_page_html(request, result, isinstance(user_controller.get_profile(username),
                                                              Profile) and 'user_profile.html' or 'business_profile.html',
                                  'profile' in result.data and result.data['profile'].name or '',
                                  'profile' in result.data and result.data['profile'].Bio or ''),
)
def user_profile(request, username):
    result = ResponseResult()
    profile = request.validation_result.data['profile']

    result.data['profile'] = profile
    result.data['is_owner'] = request.user.is_authenticated() and request.user.pk == profile.user.pk

    result.data['offers_count'] = Trade.objects.get_valid_trades(types=[POST_TYPE_OFFER]).filter(OwnerUser=profile.user).count()
    result.data['listeners_count'] = stream_controller.get_stream_listeners(stream=profile.stream2, count_only=True)

    if request.user.is_authenticated():
        result.data['is_listening'] = user_controller.is_listening(request.user, profile.stream2)

    if isinstance(profile, Profile):
        result.data['requests_count'] = Trade.objects.get_valid_trades(types=[POST_TYPE_REQUEST]).filter(OwnerUser=profile.user).count()
        result.data['experiences_count'] = experience_controller.GetExperiencesCount(profile)
        result.data['listening_count'] = {
            'users': stream_controller.get_user_listening(user=profile.user, listening_type=STREAM2_TYPE_PROFILE, count_only=True),
            'tags': stream_controller.get_user_listening(user=profile.user, listening_type=STREAM2_TYPE_TAG, count_only=True),
        }
        result.data['listening_count']['all'] = result.data['listening_count']['users'] + result.data['listening_count']['tags']
        fb_la = hasattr(profile.user, 'linked_facebook') and profile.user.linked_facebook or None
        result.data['user_profile_fb'] = ('https://www.facebook.com/profile.php?id=' + str(fb_la.facebook_id)) if fb_la else None
        result.data['fb_og_type'] = 'user'

    if isinstance(profile, Business):
        thumps_count = experience_controller.GetBusinessThumbsCount(profile)
        result.data['thumb_up_count'] = thumps_count['ups']
        result.data['thumb_down_count'] = thumps_count['downs']
        result.data['recent_experiences'] = experience_controller.GetExperiences(user=request.user, about_business=profile, start_index=0,
                                                                                 end_index=5)
        if request.user == profile.user:
            result.data['item_form'] = ItemForm()
            result.data['IsOwner'] = 1
        else:
            result.data['IsOwner'] = 0
        result.data['fb_og_type'] = 'business'

    result.data['report_form'] = ReportForm()
    result.data['is_fb_og'] = True
    result.data['fb_og_url'] = user_link(profile.user)
    return result


@non_cached_view(methods=['GET', 'POST', 'DELETE'], login_required=True, api_renderer=push_user_api, validator=push_validator)
def push(request, username, push_type):
    result = ResponseResult()

    if request.method == 'POST':
        token = request.validation_result.data['token']
        if push_type == 'apns':
            try:
                existing_apns_device = APNSDevice.objects.get(registration_id=token)
            except APNSDevice.DoesNotExist:
                existing_apns_device = None
            user_apns_device = request.user.apns_device
            if existing_apns_device:
                existing_apns_device.user = request.user
                existing_apns_device.save()
            elif user_apns_device:
                user_apns_device.registration_id = token
                user_apns_device.save()
            else:
                user_apns_device = APNSDevice(registration_id=token, user=request.user)
                user_apns_device.save()

        elif push_type == 'gcm':
            try:
                existing_gcm_device = APNSDevice.objects.get(registration_id=token)
            except APNSDevice.DoesNotExist:
                existing_gcm_device = None
            user_gcm_device = request.user.gcm_device
            if existing_gcm_device:
                existing_gcm_device.user = request.user
                existing_gcm_device.save()
            if user_gcm_device:
                user_gcm_device.registration_id = token
                user_gcm_device.save()
            else:
                user_gcm_device = GCMDevice(registration_id=token, user=request.user)
                user_gcm_device.save()

    elif request.method == 'DELETE':
        if push_type == 'apns':
            user_apns_device = request.user.apns_device
            if user_apns_device:
                user_apns_device.delete()

        elif push_type == 'gcm':
            user_gcm_device = request.user.gcm_device
            if user_gcm_device:
                user_gcm_device.delete()

    return result


@non_cached_view(methods=['GET'], json_renderer=json_data_renderer, api_renderer=stats_api, validator=user_profile_validator)
def user_stats(request, username, stats_type, listening_type='all', period='recent'):
    result = ResponseResult()
    profile = request.validation_result.data['profile']

    # todo: period usage
    if stats_type == 'listeners':
        listeners = stream_controller.get_stream_listeners(profile.stream2)

        if hasattr(request, 'is_api') and request.is_api:
            result.data['listeners'] = listeners
        else:
            # todo: minimize the db queries
            result.data['listeners'] = [
                {'username': user.username, 'name': user.name, 'image': thumbnail(user.profile.image, 32)}
                for user in listeners]

    elif stats_type == 'listening':
        result.data['listening'] = {}
        listening_tags = listening_type == 'all' or listening_type == 'tags'
        listening_profiles = listening_type == 'all' or listening_type == 'users'

        if listening_tags:
            listening_tags = stream_controller.get_user_listening(profile.user, STREAM2_TYPE_TAG)
        if listening_profiles:
            listening_profiles = stream_controller.get_user_listening(profile.user, STREAM2_TYPE_PROFILE)

        if hasattr(request, 'is_api') and request.is_api:
            if listening_tags or listening_tags == []:
                result.data['listening']['tags'] = listening_tags
            if listening_profiles or listening_profiles == []:
                result.data['listening']['users'] = listening_profiles
        else:
            # todo: minimize the db queries
            # in the case of empty array the user requested this state so return it even if it is empty
            if listening_tags or listening_tags == []:
                result.data['listening']['tags'] = [tag.Name for tag in listening_tags]
            if listening_profiles or listening_profiles == []:
                result.data['listening']['users'] = [
                    {'username': p.username, 'name': p.name, 'image': thumbnail(p.image, 32)}
                    for p in listening_profiles]
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
    if 'emails' in request.POST:
        emails = request.POST.getlist('emails')
    elif 'emails[]' in request.POST:
        emails = request.POST.getlist('emails[]')

    if emails:
        names_emails_dict = {email.split('|')[0]: email.split('|')[1] for email in emails}
        email_controller.SendInvitationEmail(request.user, names_emails_dict)

    return result


@non_cached_view(methods=['GET'],
                 validator=user_profile_validator,
                 api_renderer=shouts_api,
                 json_renderer=lambda request, result, *args, **kwargs: user_stream_json(request, result)
)
def user_stream(request, username):
    result = ResponseResult()
    profile = request.validation_result.data['profile']
    page_num = int(request.GET.get('page', 1))
    start_index = DEFAULT_PAGE_SIZE * (page_num - 1)
    end_index = DEFAULT_PAGE_SIZE * page_num

    # result.data['shouts_count2'] = profile.Stream.Posts.filter(Q(Type=POST_TYPE_REQUEST) | Q(Type=POST_TYPE_OFFER)).count()
    # result.data['shouts2'] = stream_controller.GetStreamShouts(profile.Stream, DEFAULT_PAGE_SIZE * (page_num - 1), DEFAULT_PAGE_SIZE * page_num)

    result.data['shouts_count'] = stream_controller.get_stream_shouts_count(profile.Stream)
    result.data['shouts'] = stream_controller.get_stream_shouts(profile.Stream, start_index, end_index)

    result.data['pages_count'] = int(math.ceil(result.data['shouts_count'] / float(DEFAULT_PAGE_SIZE)))
    result.data['is_last_page'] = page_num == result.data['pages_count']

    return result


@non_cached_view(methods=['GET'],
                 validator=user_profile_validator,
                 api_renderer=activities_api,
                 json_renderer=lambda request, result, *args, **kwargs: activities_stream_json(request, result))
def activities_stream(request, username):
    result = ResponseResult()
    profile = request.validation_result.data['profile']
    page_num = int(request.GET.get('page', 1))
    start_index = DEFAULT_PAGE_SIZE * (page_num - 1)
    end_index = DEFAULT_PAGE_SIZE * page_num

    post_count, stream_posts = user_controller.activities_stream(profile, start_index, end_index)
    result.data['pages_count'] = int(math.ceil(post_count / float(DEFAULT_PAGE_SIZE)))
    result.data['is_last_page'] = page_num >= result.data['pages_count']
    result.data['posts'] = stream_posts
    return result
