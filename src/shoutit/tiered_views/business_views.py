from django.forms.utils import ErrorDict, ErrorList
from django.utils.translation import ugettext as _
from django.conf import settings

from shoutit.models import User
from common.constants import TOKEN_LONG, TOKEN_TYPE_EMAIL_BUSINESS_ACTIVATE, \
    BUSINESS_CONFIRMATION_STATUS_WAITING, \
    BUSINESS_CONFIRMATION_STATUS_WAITING_PAYMENT, BUSINESS_CONFIRMATION_STATUS_WAITING_CONFIRMATION, \
    BUSINESS_CONFIRMATION_STATUS_WAITING_PAYMENT_CONFIRMATION
from shoutit.forms import BusinessSignUpForm, StartBusinessForm, BusinessEditProfileForm, \
    CreateTinyBusinessForm, RecoverForm, \
    BusinessTempSignUpForm
from shoutit.models import ConfirmToken, Business
from shoutit.permissions import ANONYMOUS_USER_PERMISSIONS
from shoutit.tiered_views.renderers import page_html, json_renderer, confirm_business_renderer_json, \
    edit_profile_renderer_json, \
    create_tiny_business_renderer_json
from shoutit.tiered_views.validators import form_validator, user_edit_profile_validator
from shoutit.controllers import business_controller, payment_controller, email_controller, \
    user_controller
from shoutit.tiers import non_cached_view, ResponseResult, RESPONSE_RESULT_ERROR_REDIRECT, \
    RESPONSE_RESULT_ERROR_BAD_REQUEST


@non_cached_view(
    html_renderer=lambda request, result, tiny_username: page_html(request, result,
                                                                   'signup_temp_business.html',
                                                                   'Sign Up Business'),
    json_renderer=lambda request, result, tiny_username:
    json_renderer(request, result, success_message=_(
        'Well done, now check your e-mail inbox and follow the instructions')),
    methods=['GET', 'POST'],
    validator=lambda request, *args, **kwargs: form_validator(request, BusinessTempSignUpForm))
def signup_temp(request, tiny_username=None):
    result = ResponseResult()
    business = None
    init = {}
    result = ResponseResult()
    if tiny_username and len(tiny_username) > 0:
        business = business_controller.GetBusiness(tiny_username)
        if not business or business.Confirmed:
            result.errors.append(RESPONSE_RESULT_ERROR_REDIRECT)
            result.data['next'] = '/btempsignup/'
            return result
        init = {'name': business.name}
    if request.method == 'POST':
        form = BusinessTempSignUpForm(request.POST, request.FILES, initial=init)
        form.is_valid()

        user = business_controller.SignUpTempBusiness(request, form.cleaned_data['email'],
                                                      form.cleaned_data['password'], True, business)
        user_controller.give_user_permissions(user, ANONYMOUS_USER_PERMISSIONS)
    else:
        form = BusinessTempSignUpForm(initial=init)

    if business:
        result.data['business'] = business
    result.data['form'] = form
    return result


@non_cached_view(
    html_renderer=lambda request, result, token: page_html(request, result, result.data['template'],
                                                           'Sign Up Business'),
    json_renderer=lambda request, result, token: json_renderer(request,
                                                               result,
                                                               success_message=_(
                                                                   'Well done, now check your e-mail inbox and follow the instructions')),
    methods=['GET', 'POST'], )
def signup(request, token=None):
    business = None
    result = ResponseResult()
    business_init = {}
    user = None
    if 'business_user_id' in request.session:
        user = User.objects.filter(pk=request.session['business_user_id'])
        if not user:
            del request.session['business_user_id']
            result.errors.append(RESPONSE_RESULT_ERROR_REDIRECT)
            result.data['next'] = '/'
            return result
        else:
            user = user[0]
    else:
        result.errors.append(RESPONSE_RESULT_ERROR_REDIRECT)
        result.data['next'] = '/'
        return result

    if not user.BusinessCreateApplication.count():
        result.errors.append(RESPONSE_RESULT_ERROR_REDIRECT)
        result.data['next'] = '/'
        return result

    application = user.BusinessCreateApplication.all()[0]

    if application.Status == BUSINESS_CONFIRMATION_STATUS_WAITING:
        result.data['template'] = 'signup_business.html'
        init = {'email': user.email}
        if not user.is_authenticated() or (user.is_authenticated() and user.abstract_profile):
            result.errors.append(RESPONSE_RESULT_ERROR_REDIRECT)
            result.data['next'] = '/'
            return result

        lat = None
        lng = None

        if application.Business:
            business = application.Business
            business_init = {'name': business.name,
                             'category': application.Category and application.Category.pk or 0,
                             'location': unicode(business.latitude) + ', ' + unicode(
                                 business.longitude), 'city': business.city,
                             'country': business.country}
            lat = business.latitude
            lng = business.longitude
        else:
            business_init = {'name': application.name,
                             'category': application.Category and application.Category.pk or 0,
                             'location': unicode(application.latitude) + ', ' + unicode(
                                 application.longitude), 'city': application.city,
                             'country': application.country}
            init.update({'phone': application.Phone, 'description': application.About,
                         'website': application.Website})
            lat = application.latitude
            lng = application.longitude

        if request.method == 'POST':
            form = BusinessSignUpForm(request.POST, request.FILES, initial=init)
            tiny_business_form = CreateTinyBusinessForm(request.POST, initial=business_init)

            files = []
            if 'business_documents[]' in request.POST:
                files = request.POST.getlist('business_documents[]')
            elif 'business_documents' in request.POST:
                files = request.POST.getlist('business_documents')

            if not len(files):
                result.errors.append(RESPONSE_RESULT_ERROR_BAD_REQUEST)
                result.form_errors = ErrorDict(
                    {'business_documents': ErrorList(_('You should upload documents to continue'))})
                return result
            if form.is_valid() and tiny_business_form.is_valid():
                if business:
                    lat = business.latitude
                    lng = business.longitude
                    category = business.Category and business.Category.pk or None
                    city = business.city
                    country = business.country
                    address = business.address
                else:
                    latlng = tiny_business_form.cleaned_data['location']
                    lat = len(latlng.split(',')) and latlng.split(',')[0].strip() or 0
                    lng = len(latlng.split(',')) and latlng.split(',')[1].strip() or 0
                    category = tiny_business_form.cleaned_data['category']
                    city = tiny_business_form.cleaned_data['city']
                    country = tiny_business_form.cleaned_data['country']
                    address = tiny_business_form.cleaned_data['address']

                application = business_controller.SignUpBusiness(request, user,
                                                                 tiny_business_form.cleaned_data[
                                                                     'name'],
                                                                 form.cleaned_data['phone'],
                                                                 form.cleaned_data['website'],
                                                                 category,
                                                                 form.cleaned_data['description'],
                                                                 latitude=lat, longitude=lng,
                                                                 country=country,
                                                                 city=city, address=address,
                                                                 documents=files)
                application.Status = BUSINESS_CONFIRMATION_STATUS_WAITING_CONFIRMATION
                application.save()
                result.errors.append(RESPONSE_RESULT_ERROR_REDIRECT)
                result.data['next'] = '/bsignup/'
            else:
                result.errors.append(RESPONSE_RESULT_ERROR_BAD_REQUEST)
                result.messages.append(('error', _('You have entered some invalid input.')))
                result.form_errors.update(form.errors)
                result.form_errors.update(tiny_business_form.errors)
                return result
        else:
            form = BusinessSignUpForm(initial=init)
            tiny_business_form = CreateTinyBusinessForm(initial=business_init)

        if business:
            result.data['business'] = business
        if lat and lng:
            result.data['lat'] = lat
            result.data['lng'] = lng
        result.data['form'] = form
        result.data['tiny_business_form'] = tiny_business_form
    elif application.Status == BUSINESS_CONFIRMATION_STATUS_WAITING_PAYMENT:
        if token and payment_controller.CheckPaymentToken(user, 'subscription', token):
            application.Status = BUSINESS_CONFIRMATION_STATUS_WAITING_PAYMENT_CONFIRMATION
            application.save()
            result.data['template'] = 'wait_business.html'
            result.data['message'] = _(
                'We are still working on confirming your payment, please come back later, thanks.')
        else:
            result.errors.append(RESPONSE_RESULT_ERROR_REDIRECT)
            result.data['next'] = '/subscribe/'
            return result
    elif application.Status == BUSINESS_CONFIRMATION_STATUS_WAITING_PAYMENT_CONFIRMATION:
        result.data['template'] = 'wait_business.html'
        result.data['message'] = _(
            'We are still working on confirming your payment, please come back later, thanks.')
    elif application.Status == BUSINESS_CONFIRMATION_STATUS_WAITING_CONFIRMATION:
        result.data['template'] = 'wait_business.html'
        result.data['message'] = _(
            'We are still working on confirming your profile, please come back later, thanks.')

    return result


@non_cached_view(methods=['POST'],
                 validator=lambda request, *args, **kwargs: form_validator(request, RecoverForm,
                                                                           message=_(
                                                                               'email does not exist.')),
                 json_renderer=lambda request, result, *args, **kwargs: json_renderer(request,
                                                                                      result,
                                                                                      _(
                                                                                          'We sent you a new email to activate your account.')))
def recover_activation(request):
    result = ResponseResult()
    form = RecoverForm(request.POST)
    form.is_valid()
    email = form.cleaned_data['username_or_email']
    profile = user_controller.GetUserByEmail(email)
    if not profile:
        result.errors.append(RESPONSE_RESULT_ERROR_BAD_REQUEST)
        return result
    if not isinstance(profile, Business):
        result.errors.append(RESPONSE_RESULT_ERROR_BAD_REQUEST)
        return result
    user = profile.user
    email = user.email
    token = user_controller.set_last_token(user, email, TOKEN_LONG,
                                           TOKEN_TYPE_EMAIL_BUSINESS_ACTIVATE)
    email_controller.SendEmail(email, {
        'name': profile.name,
        'link': settings.SITE_LINK + token
    }, '', '')
    return result


@non_cached_view(
    json_renderer=lambda request, result, *args: create_tiny_business_renderer_json(request,
                                                                                    result),
    methods=['GET', 'POST'], post_login_required=True)
def create_tiny_business(request):
    if request.method == 'POST':
        form = CreateTinyBusinessForm(request.POST)
        form.is_valid()

        business_controller.CreateTinyBusinessProfile(form.cleaned_data['name'],
                                                      'category' in form.cleaned_data and
                                                      form.cleaned_data['category'] or None,
                                                      'latitude' in form.cleaned_data and
                                                      form.cleaned_data['latitude'] or 0.0,
                                                      'longitude' in form.cleaned_data and
                                                      form.cleaned_data['longitude'] or 0.0,
                                                      'country' in form.cleaned_data and
                                                      form.cleaned_data['country'] or None,
                                                      'city' in form.cleaned_data and
                                                      form.cleaned_data['city'] or None,
                                                      'address' in form.cleaned_data and
                                                      form.cleaned_data['address'] or None)
    else:
        form = CreateTinyBusinessForm()
    result = ResponseResult()
    result.data['form'] = form
    return result


@non_cached_view(
    json_renderer=lambda request, result, *args: confirm_business_renderer_json(request, result),
    methods=['GET', 'POST'])
def confirm_business(request):
    result = ResponseResult()
    if hasattr(request, 'session') and hasattr(request.session, 'session_key'):
        token = request.COOKIES.get('bc_t_' + request.session.session_key, None)
    else:
        token = None

    if token is None:
        result.errors.append(RESPONSE_RESULT_ERROR_REDIRECT)
        result.data['next'] = '/'
        return result

    user = user_controller.GetUserByToken(token, True, False)
    if user is None:
        result.errors.append(RESPONSE_RESULT_ERROR_REDIRECT)
        result.data['next'] = '/'
        return result

    profile = user.abstract_profile
    if profile is None or not isinstance(profile, Business):
        result.errors.append(RESPONSE_RESULT_ERROR_REDIRECT)
        result.data['next'] = '/'
        return result

    if profile.Confirmed:
        result.messages.append(('error', _("You are already confirmed")))
        result.errors.append(RESPONSE_RESULT_ERROR_REDIRECT)
        return result

    t = ConfirmToken.getToken(token, True, False)

    if not t:
        result.errors.append(RESPONSE_RESULT_ERROR_REDIRECT)
        return result

    type = t.type
    source_email = None
    if t.Email and t.Email.strip() != '':
        source_email = t.Email

    email = user.email
    if source_email:
        email = source_email

    if request.method == 'POST':
        init = {'name': profile.name, 'username': user.username, 'email': user.email,
                'phone': profile.Phone, 'tokentype': type}
        form = StartBusinessForm(request.POST, request.FILES, initial=init)
        if not form.is_valid():
            result.errors.append(RESPONSE_RESULT_ERROR_BAD_REQUEST)
            result.form_errors = form.errors
            return result

        user.username = form.cleaned_data['username']
        user.set_password(form.cleaned_data['password'])
        profile.Confirmed = True
        user.save()
        profile.save()
    # result.data['next'] = '/user/' + user.username
    else:
        init = {'name': profile.name, 'username': user.username, 'email': email,
                'phone': profile.Phone, 'tokentype': type}
        form = StartBusinessForm(initial=init)
    result.data['form'] = form
    return result


@non_cached_view(
    json_renderer=edit_profile_renderer_json,
    login_required=True,
    validator=lambda request, username: user_edit_profile_validator(request, username,
                                                                    user_controller.get_profile(
                                                                        username).user.email),
)
def business_edit_profile(request, username):
    profile = user_controller.get_profile(username)
    result = ResponseResult()
    result.data['profile'] = profile
    if request.method == 'POST':
        form = BusinessEditProfileForm(request.POST, request.FILES,
                                       initial={'username': username, 'email': profile.user.email})
        form.is_valid()

        if 'username' in form.cleaned_data and form.cleaned_data['username']:
            profile.user.username = form.cleaned_data['username']
            result.data['next'] = '/user/' + form.cleaned_data['username'] + '/'
        if 'email' in form.cleaned_data and form.cleaned_data['email']:
            profile.user.email = form.cleaned_data['email']
        if 'name' in form.cleaned_data and form.cleaned_data['name']:
            profile.user.first_name = form.cleaned_data['name']
        if 'website' in form.cleaned_data and form.cleaned_data['website']:
            profile.Website = form.cleaned_data['website']

        if 'location' in form.cleaned_data and form.cleaned_data['location']:
            latlng = form.cleaned_data['location']
            latitude = float(latlng.split(',')[0].strip())
            longitude = float(latlng.split(',')[1].strip())
            city = form.cleaned_data['city']
            country = form.cleaned_data['country']
            address = form.cleaned_data['address']

            profile.latitude = latitude
            profile.longitude = longitude
            profile.city = city
            profile.country = country
            profile.address = address

        profile.bio = form.cleaned_data['bio']
        if 'password' in form.cleaned_data and form.cleaned_data['password']:
            profile.user.set_password(form.cleaned_data['password'])

        profile.user.save()
        profile.save()
        result.messages.append(('success', _('Your profile was updated successfully.')))
    else:
        form = BusinessEditProfileForm(
            initial={'email': profile.email, 'bio': profile.bio, 'username': profile.username,
                     'name': profile.name,
                     'website': profile.Website})
    result.data['form'] = form
    return result


@non_cached_view(
    html_renderer=lambda request, result: page_html(request, result, result.data['template'],
                                                    'Subscribe Business'),
    methods=['GET'], )
def subscribe(request):
    result = ResponseResult()
    user = None
    if 'business_user_id' in request.session:
        user = User.objects.filter(pk=request.session['business_user_id'])
        if not user:
            del request.session['business_user_id']
            result.errors.append(RESPONSE_RESULT_ERROR_REDIRECT)
            result.data['next'] = '/'
            return result
        else:
            user = user[0]
    elif request.user.is_authenticated():
        if isinstance(request.user.abstract_profile,
                      Business) and request.user.BusinessCreateApplication.all():
            user = request.user
        else:
            result.errors.append(RESPONSE_RESULT_ERROR_REDIRECT)
            result.data['next'] = '/'
            return result
    else:
        result.errors.append(RESPONSE_RESULT_ERROR_REDIRECT)
        result.data['next'] = '/'
        return result

    if not user.BusinessCreateApplication.count():
        result.errors.append(RESPONSE_RESULT_ERROR_REDIRECT)
        result.data['next'] = '/'
        return result

    application = user.BusinessCreateApplication.all()[0]

    if BUSINESS_CONFIRMATION_STATUS_WAITING_PAYMENT != application.Status:
        result.errors.append(RESPONSE_RESULT_ERROR_REDIRECT)
        result.data['next'] = '/'
        return result

    result.data['template'] = 'pay_business.html'
    result.data['subscription_form'] = payment_controller.GetPaypalFormForSubscription(user)
    return result
