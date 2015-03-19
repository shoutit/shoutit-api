import os
from django.contrib import messages
from django.http import HttpResponseRedirect, Http404, HttpResponse
from django.shortcuts import render_to_response
from django.template.context import RequestContext
from django.template.loader import render_to_string
from django.utils.translation import ugettext_lazy as _
from django.conf import settings

from common.constants import ENUM_XHR_RESULT, MESSAGE_HEAD, POST_TYPE_EXPERIENCE, DEFAULT_LOCATION
from shoutit.models import ConfirmToken, Profile, Business, Trade, PredefinedCity
from shoutit.permissions import PERMISSION_ACTIVATED
from shoutit.tiers import RESPONSE_RESULT_ERROR_NOT_LOGGED_IN, RESPONSE_RESULT_ERROR_NOT_ACTIVATED, RESPONSE_RESULT_ERROR_REDIRECT, \
    RESPONSE_RESULT_ERROR_BAD_REQUEST, RESPONSE_RESULT_ERROR_404, RESPONSE_RESULT_ERROR_FORBIDDEN, RESPONSE_RESULT_ERROR_PERMISSION_NEEDED
from shoutit.utils import shout_link
from shoutit.xhr_utils import xhr_respond, redirect_to_modal_xhr
from common import constants
from shoutit.controllers import user_controller
from shoutit.templatetags import template_filters


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
            RESPONSE_RESULT_ERROR_PERMISSION_NEEDED in result.errors and PERMISSION_ACTIVATED in result.missing_permissions):
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


def user_stream_json(request, result):
    if not result.errors:
        types = 'shout_types[]' in request.GET and request.GET.getlist('shout_types[]') or []

        if POST_TYPE_EXPERIENCE in types and len(types) == 1:
            variables = {
                'experiences': result.data['experiences']
            }
            variables = RequestContext(request, variables)
            data = {'html': render_to_string("experiences_stream.html", variables)}
            for k, v in result.data.iteritems():
                if k != 'experiences':
                    data[k] = v
            data['count'] = len(variables['experiences'])
            return xhr_respond(ENUM_XHR_RESULT.SUCCESS, '', data=data)

        variables = {
            'shouts': result.data['shouts']
        }
        variables = RequestContext(request, variables)
        data = {'html': render_to_string("stream.html", variables)}
        for k, v in result.data.iteritems():
            if k != 'shouts':
                data[k] = v
        data['count'] = len(variables['shouts'])
        return xhr_respond(ENUM_XHR_RESULT.SUCCESS, '', data=data)

    else:
        return get_initial_json_response(request, result, _('User not found'))


def conversation_json(request, result):
    if not result.errors:
        variables = {
            'form': result.data['form'],
            'conversation': result.data['conversation'],
            'shout': result.data['shout'],
            'conversation_messages': result.data['conversation_messages'],
            'conversation_id': result.data['conversation_id'],
            'title': result.data['title'],
        }
        variables = RequestContext(request, variables)
        data = {'conversation_messages_html': render_to_string("conversation_messages.html", variables),
                'conversation_shout_html': render_to_string("shout_detailed.html", variables)
        }
        return xhr_respond(ENUM_XHR_RESULT.SUCCESS, '', data=data)
    else:
        return get_initial_json_response(request, result)


def json_send_message(request, result):
    if not result.errors:
        variables = {
            'message': result.data['message'],
        }
        variables = RequestContext(request, variables)
        data = {'html': render_to_string("message.html", variables),
                'conversation_id': result.data['message'].Conversation_id}
        return xhr_respond(ENUM_XHR_RESULT.SUCCESS, '', data=data)
    else:
        return get_initial_json_response(request, result, _('You need to enter some text!'))


def json_data_renderer(request, result, *args, **kwargs):
    if not result.errors:
        return xhr_respond(ENUM_XHR_RESULT.SUCCESS, '', {}, result.data)
    else:
        return get_initial_json_response(request, result)


def index_html(request, result, browse_type=None):
    return HttpResponseRedirect('/%s/%s/' % (result.data['browse_type'], result.data['browse_city']))


def browse_html(request, result, browse_type, url_encoded_city, browse_category=None):
    if 'redirect_category' in result.data:
        return HttpResponseRedirect('/%s/%s/' % (browse_type, url_encoded_city))
    if 'redirect_city' in result.data:
        redirect_city = '/%s/%s/' % (browse_type, result.data['browse_city_encoded'])
        if browse_category:
            redirect_city += '%s/' % browse_category
        return HttpResponseRedirect(redirect_city)
    profile = None
    page_title = unicode.title(u"%s%s %s" % (result.data['browse_city'], (" %s" % browse_category) if browse_category else '', browse_type))
    if not browse_category:
        page_desc = _(
            'Shoutit is a social marketplace where buyers and sellers from %(city)s meet. Post or ask for Cars, Electronics, Properties, Food, or Jobs in %(city)s ') % {
                    'city': result.data['browse_city']}
    else:
        page_desc = _(
            'Shoutit is a social marketplace where buyers and sellers from %(city)s meet. Post or ask about %(category)s in %(city)s.') % {
                    'city': result.data['browse_city'], 'category': unicode.title(browse_category)}

    if request.user.is_authenticated():
        profile = request.user.abstract_profile
    if profile and isinstance(profile, Business):
        return page_html(request, result, 'business_browse.html', page_title, page_desc)
    return page_html(request, result, 'browse.html', page_title, page_desc)


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


def thumbnail_response(request, result, *args, **kwargs):
    if RESPONSE_RESULT_ERROR_BAD_REQUEST in result.errors:
        raise Http404()

    from PIL.Image import open as image_open, ANTIALIAS

    if result.data['size']:
        path = '%s_%dx%d.png' % (
            os.path.splitext(result.data['picture'])[0], result.data['size'][0], result.data['size'][0])
    else:
        path = result.data['picture']
    if os.path.exists(path):
        im = image_open(path)
    else:
        im = image_open(result.data['picture'])
        if result.data['size']:
            im.thumbnail(result.data['size'], ANTIALIAS)
            im.save(path, "PNG")
        else:
            raise Http404()
    response = HttpResponse(content_type="image/png")
    im.save(response, "PNG")
    response['Content-Length'] = len(response.content)
    return response


def signin_renderer_json(request, result):
    if request.method == 'POST':
        return json_renderer(request, result, success_message=_('You are now logged in.'),
                             data={'next': 'next' in result.data and result.data['next'] or '/',
                                   'username': 'username' in result.data and result.data['username'] or ''})
    else:
        variables = RequestContext(request, result.data)
        return render_to_response('xhr_sign_in.html', variables)


def notifications_json(request, result, *args, **kwargs):
    variables = {constant: getattr(constants, constant) for constant in dir(constants) if
                 constant.startswith('NOTIFICATION_TYPE_')}
    return render_to_response('notifications.html', RequestContext(request, variables))


def notifications_html(request, result, *args, **kwargs):
    result.data.update({constant: getattr(constants, constant) for constant in dir(constants) if
                        constant.startswith('NOTIFICATION_TYPE_')})
    return page_html(request, result, 'notifications_page.html', _('Notifications'))


def shout_brief_json(request, result, *args):
    if not result.errors:
        variables = {
            'shout': result.data['shout']
        }
        variables = RequestContext(request, variables)
        data = {'html': render_to_string('shout_brief.html', variables)}
        return xhr_respond(ENUM_XHR_RESULT.SUCCESS, '', data=data)
    else:
        return get_initial_json_response(request, result)


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


def activate_renderer_json(request, result):
    if request.method == 'POST':
        response = json_renderer(request, result, success_message=_('You are now activated.'),
                                 data={'next': 'next' in result.data and result.data['next'] or '/'})

        return response
    else:
        if result.errors:
            return json_renderer(request, result, success_message=_('Activation'),
                                 data={'next': 'next' in result.data and result.data['next'] or '/'})
        variables = RequestContext(request, result.data)
        response = render_to_response('activate_user.html', variables)
        return response


def resend_activation_json(request, result):
    if request.method == 'POST':
        return json_renderer(request, result, success_message=_('An activation message will be sent to your email soon.'),
                             data={'next': 'next' in result.data and result.data['next'] or '/'})
    else:
        if result.errors:
            return json_renderer(request, result, success_message=_('Resend Activation'),
                                 data={'next': 'next' in result.data and result.data['next'] or '/'})
        variables = RequestContext(request, result.data)
        return render_to_response('modals/resend_activation_modal.html', variables)


def activate_modal_html(request, result, token):
    if not result.errors:
        t = ConfirmToken.getToken(token, True, False)
        user = t.user
        profile = user.abstract_profile

        if t and (isinstance(profile, Profile) and not request.user.profile.isSSS) or (isinstance(profile, Business)) or (
        user.BusinessCreateApplication.count()):
            t.disable()

        link = settings.SITE_LINK

        if t.type == int(constants.TOKEN_TYPE_HTML_EMAIL_BUSINESS_ACTIVATE):
            request.session['business_user_id'] = user.pk
            response = HttpResponseRedirect('/bsignup/')
            response.set_cookie('ba_t_' + request.session.session_key, token)
            return response

        if t.type == int(constants.TOKEN_TYPE_HTML_EMAIL_BUSINESS_CONFIRM):
            response = HttpResponseRedirect(link + '#confirm_business')
            response.set_cookie('bc_t_' + request.session.session_key, token)
            return response

        shout = Trade.objects.get_valid_trades().filter(user=t.user)
        if len(shout):
            url = shout_link(shout[0])
        else:
            url = link

        if t.type == int(constants.TOKEN_TYPE_RECOVER_PASSWORD) and request.user.is_authenticated():
            response = HttpResponseRedirect(link + 'user/' + request.user.username + '/#edit')
            return response

        response = HttpResponseRedirect(url + '#activate')
        response.set_cookie('a_t_' + str(t.user.username), token)

        return response
    return HttpResponseRedirect('/')


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


def read_conversations_stream_json(request, result):
    if not result.errors:
        variables = {
            'conversations': result.data['conversations'],
        }
        variables = RequestContext(request, variables)
        data = {'html': render_to_string('conversations_stream.html', variables)}
        for k, v in result.data.iteritems():
            if k != 'conversations':
                data[k] = v
        data['count'] = len(variables['conversations'])
        return xhr_respond(ENUM_XHR_RESULT.SUCCESS, '', data=data)
    else:
        return get_initial_json_response(request, result)


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
            'state': int(result.data['experience'].State),
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
            'date': result.data['comment'].DateCreated.strftime('%d/%m/%Y %H:%M:%S%z')
        }
        return xhr_respond(ENUM_XHR_RESULT.SUCCESS, message=message, data=data)
    else:
        return get_initial_json_response(request, result)


def profile_json_renderer(request, result):
    if not result.errors:
        data = {
            'users': [
                {
                    'username': user.username,
                    'name': user.name,
                    'category_id': isinstance(user.abstract_profile, Business) and user.profile.Category.pk or None,
                    'about': user.Bio,
                    'lat': user.latitude,
                    'lng': user.longitude,
                    'city': user.city,
                    'country': user.country,
                    'image': user.abstract_profile.image,
                    'source': user.has_source() and user.Source.Source or int(constants.BUSINESS_SOURCE_TYPE_NONE),
                    'source_id': user.has_source() and user.Source.SourceID or None
                } for user in result.data['users']
            ]
        }
        return xhr_respond(ENUM_XHR_RESULT.SUCCESS, '', data=data)
    else:
        return get_initial_json_response(request, result)


def user_json_renderer(request, result):
    if not result.errors:
        data = {
            'users': [
                {
                    'username': user.username,
                    'name': user.name,
                    'image': template_filters.thumbnail(user.abstract_profile.image, 32)
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
                    'date': comment.DateCreated.strftime('%d/%m/%Y %H:%M:%S%z')
                } for comment in result.data['comments']]
        }
        return xhr_respond(ENUM_XHR_RESULT.SUCCESS, '', data=data)
    else:
        return get_initial_json_response(request, result)


def live_events_json_renderer(request, result):
    if not result.errors:
        events_arr = []
        for event in result.data['events']:
            variables = {
                'event': event,
                'event_types': constants.EventType.texts
            }
            variables = RequestContext(request, variables)
            events_arr.append({'id': event.pk, 'html': render_to_string("event.html", variables)})
        data = {
            'events': events_arr,
            'count': result.data['count'],
            'timestamp': result.data['timestamp']
        }
        return xhr_respond(ENUM_XHR_RESULT.SUCCESS, '', data=data)
    else:
        return get_initial_json_response(request, result)
