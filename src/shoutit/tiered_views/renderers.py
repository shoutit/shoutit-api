from django.contrib import messages
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template.context import RequestContext
from django.template.loader import render_to_string
from django.utils.translation import ugettext_lazy as _
from django.conf import settings

from common.constants import ENUM_XHR_RESULT, MESSAGE_HEAD, DEFAULT_LOCATION
from shoutit.models import Profile, Business, PredefinedCity
from shoutit.tiers import RESPONSE_RESULT_ERROR_NOT_LOGGED_IN, RESPONSE_RESULT_ERROR_NOT_ACTIVATED, RESPONSE_RESULT_ERROR_REDIRECT, \
    RESPONSE_RESULT_ERROR_BAD_REQUEST, RESPONSE_RESULT_ERROR_FORBIDDEN, RESPONSE_RESULT_ERROR_PERMISSION_NEEDED
from shoutit.utils import shout_link
from shoutit.xhr_utils import xhr_respond, redirect_to_modal_xhr
from common import constants


def render_in_master_page(request, template, variables, page_title='', page_desc=''):
    variables['page_title'] = page_title
    if page_desc is None or page_desc == '':
        page_desc = _(
            'Shoutit is the region\'s first social marketplace where buyers post requests for goods or services that they need '
            'and the amount they would like to pay for them.')
    variables['page_desc'] = page_desc
    variables['MESSAGE_HEAD'] = MESSAGE_HEAD
    variables['constants'] = constants.rank_flags
    variables['report_constants'] = constants.report_types
    variables['settings'] = settings

    city = request.user.profile.city if request.user.is_authenticated() else DEFAULT_LOCATION['city']
    pre_city = PredefinedCity.objects.get(city=city)

    variables['user_lat'] = pre_city.latitude
    variables['user_lng'] = pre_city.longitude
    variables['user_country'] = pre_city.country
    variables['user_city'] = pre_city.city
    variables['user_city_encoded'] = pre_city.city_encoded

    if 'loop' in request.GET:
        variables['loop'] = True
    if 'no_ga' in request.GET:
        variables['no_ga'] = True

    variables = RequestContext(request, variables)
    return render_to_response(template, variables)


def get_initial_json_response(request, result, bad_request_message=''):
    if RESPONSE_RESULT_ERROR_NOT_LOGGED_IN in result.errors:
        return redirect_to_modal_xhr(request, '/signin/', _("You are not signed in."), 'signin')
    elif RESPONSE_RESULT_ERROR_NOT_ACTIVATED in result.errors or (
            RESPONSE_RESULT_ERROR_PERMISSION_NEEDED in result.errors and result.missing_permissions):
        return redirect_to_modal_xhr(request, '/reactivate/', _("You are not activated yet"), 'reactivate')
    elif RESPONSE_RESULT_ERROR_REDIRECT in result.errors:
        return xhr_respond(code=ENUM_XHR_RESULT.REDIRECT, message=result.messages and result.messages[0][1] or '', data={
            'link': (result.data and 'next' in result.data and result.data['next']) or (
                result.data and 'link' in result.data and result.data['link']) or '/'})
    elif RESPONSE_RESULT_ERROR_PERMISSION_NEEDED in result.errors or RESPONSE_RESULT_ERROR_FORBIDDEN in result.errors:
        return xhr_respond(ENUM_XHR_RESULT.FORBIDDEN,
                           result.messages and '\n'.join(unicode(message[1]) for message in result.messages) or '', message_type='error')
    elif RESPONSE_RESULT_ERROR_BAD_REQUEST in result.errors:
        return xhr_respond(ENUM_XHR_RESULT.BAD_REQUEST,
                           result.messages and '\n'.join(unicode(message[1]) for message in result.messages) or bad_request_message,
                           errors=result.form_errors, message_type='error')
    return None


def json_renderer(request, result, success_message='', data={}, success_message_type='success'):
    if not result.errors:
        return xhr_respond(ENUM_XHR_RESULT.SUCCESS, success_message, data=data, message_type=success_message_type)
    else:
        return get_initial_json_response(request, result)


def json_data_renderer(request, result, *args, **kwargs):
    if not result.errors:
        return xhr_respond(ENUM_XHR_RESULT.SUCCESS, '', {}, result.data)
    else:
        return get_initial_json_response(request, result)


def object_page_html(request, result, template, page_title='', page_desc=''):
    if RESPONSE_RESULT_ERROR_BAD_REQUEST in result.errors:
        return page_html(request, result, '404.html', _('Page Not Found'))
    return page_html(request, result, template, page_title, page_desc)


def page_html(request, result, template, page_title='', page_desc=''):
    for type, message in result.messages:
        if type == 'info':
            messages.info(request, message)
        elif type == 'error':
            messages.error(request, message)
        elif type == 'warn':
            messages.warning(request, message)
        elif type == 'success':
            messages.success(request, message)

    return render_in_master_page(request, template, RequestContext(request, result.data), page_title, page_desc)


def create_tiny_business_renderer_json(request, result):
    if not result.errors:
        if request.method == 'POST':
            response = json_renderer(request,
                                     result,
                                     success_message=_('Great, business profile was created.'),
                                     data={'next': 'next' in result.data and result.data['next'] or '/'})

            return response
        else:
            variables = RequestContext(request, result.data)
            response = render_to_response('modals/create_tiny_business_modal.html', variables)
            return response
    else:
        return get_initial_json_response(request, result)


def activate_business_renderer_json(request, result):
    if not result.errors:
        if request.method == 'POST':
            response = json_renderer(request, result, success_message=_('Thank you.'),
                                     data={'next': 'next' in result.data and result.data['next'] or '/'})

            return response
        else:
            variables = RequestContext(request, result.data)
            response = render_to_response('modals/activate_business_modal.html', variables)
            return response
    else:
        return get_initial_json_response(request, result)


def confirm_business_renderer_json(request, result):
    if not result.errors:
        if request.method == 'POST':
            response = json_renderer(request, result, success_message=_('Great, you can now use your account'),
                                     data={'next': 'next' in result.data and result.data['next'] or '/'})
            return response
        else:
            variables = RequestContext(request, result.data)
            response = render_to_response('modals/confirm_business_modal.html', variables)
            return response
    else:
        return get_initial_json_response(request, result)


def edit_profile_renderer_json(request, result, username):
    if request.method == 'POST':
        return json_renderer(request,
                             result,
                             success_message=_('Your profile was updated successfully.'),
                             data={'next': result.data['next'] if 'next' in result.data else '/user/' + username + '/'})
    else:
        if result.errors:
            return get_initial_json_response(request, result)
        variables = RequestContext(request, result.data)
        profile = request.user.is_authenticated() and request.user.abstract_profile or None
        if profile and isinstance(profile, Business):
            return render_to_response('business_edit_profile.html', variables)
        elif profile and isinstance(profile, Profile):
            return render_to_response('user_edit_profile.html', variables)
        return HttpResponseRedirect('/')


def experiences_json(request, result):
    if not result.errors:
        variables = {
            'experiences': result.data['experiences'],
            'form': result.data['form']
        }
        variables = RequestContext(request, variables)
        data = {'html': render_to_string('experiences.html', variables)}
        for k, v in result.data.iteritems():
            if k != 'experiences':
                data[k] = v
        return xhr_respond(ENUM_XHR_RESULT.SUCCESS, '', data=data)
    else:
        return get_initial_json_response(request, result)


def experiences_stream_json(request, result):
    if not result.errors:
        variables = {
            'experiences': result.data['experiences'],
            'comment_form': result.data['comment_form'],
            'timestamp': result.data['timestamp']
        }
        variables = RequestContext(request, variables)
        data = {
            'html': render_to_string('experiences_stream.html', variables),
            'count': len(result.data['experiences'])
        }
        return xhr_respond(ENUM_XHR_RESULT.SUCCESS, '', data=data)
    else:
        return get_initial_json_response(request, result)


def activities_stream_json(request, result):
    if not result.errors:
        variables = {
            'posts': result.data['posts'],
            'constants': constants.PostType.texts,
            'event_types': constants.EventType.texts
        }
        variables = RequestContext(request, variables)
        data = {
            'html': render_to_string('user_home_stream.html', variables),
            'count': len(result.data['posts'])
        }
        return xhr_respond(ENUM_XHR_RESULT.SUCCESS, '', data=data)
    else:
        return get_initial_json_response(request, result)


def deals_stream_json(request, result):
    if not result.errors:
        variables = {
            'deals': result.data['deals']
        }
        variables = RequestContext(request, variables)
        data = {
            'html': render_to_string('deals_stream.html', variables),
            'count': len(result.data['deals'])
        }
        return xhr_respond(ENUM_XHR_RESULT.SUCCESS, '', data=data)
    else:
        return get_initial_json_response(request, result)


def post_experience_json_renderer(request, result, message=_('Your experience was post successfully.')):
    if not result.errors:
        data = {
            'text': result.data['experience'].text,
            'state': int(result.data['experience'].state),
            'date': result.data['experience'].date_published.strftime('%d/%m/%Y %H:%M:%S%z'),
            'next': shout_link(result.data['experience'])
        }
        return xhr_respond(ENUM_XHR_RESULT.SUCCESS, message=message, data=data)
    else:
        return get_initial_json_response(request, result)


def comment_on_post_json_renderer(request, result, message=_('Your comment was post successfully.')):
    if not result.errors:
        data = {
            'id': result.data['comment'].pk,
            'text': result.data['comment'].text,
            'date': result.data['comment'].created_at.strftime('%d/%m/%Y %H:%M:%S%z')
        }
        return xhr_respond(ENUM_XHR_RESULT.SUCCESS, message=message, data=data)
    else:
        return get_initial_json_response(request, result)


def user_json_renderer(request, result):
    if not result.errors:
        data = {
            'users': [
                {
                    'username': user.username,
                    'name': user.name,
                    'image': user.abstract_profile.image
                } for user in result.data['users']
            ]
        }

        return xhr_respond(ENUM_XHR_RESULT.SUCCESS, '', data=data)
    else:
        return get_initial_json_response(request, result)


def post_comments_json_renderer(request, result):
    if not result.errors:
        data = {
            'comments': [
                {
                    'id': comment.pk,
                    'isOwner': comment.isOwner,
                    'text': comment.text,
                    'date': comment.created_at.strftime('%d/%m/%Y %H:%M:%S%z')
                } for comment in result.data['comments']]
        }
        return xhr_respond(ENUM_XHR_RESULT.SUCCESS, '', data=data)
    else:
        return get_initial_json_response(request, result)

