import os

from django.contrib import messages
from django.http import HttpResponseRedirect, Http404, HttpResponse
from django.shortcuts import render_to_response
from django.template.context import RequestContext
from django.template.loader import render_to_string
from django.utils.translation import ugettext_lazy as _
from piston3.utils import rc
from django.conf import settings

from common.constants import ENUM_XHR_RESULT, MESSAGE_HEAD, POST_TYPE_EXPERIENCE, DEFAULT_LOCATION, PostType
from apps.shoutit.controllers import user_controller
from apps.shoutit.models import Shout, ConfirmToken, Profile, Business, Trade, PredefinedCity
from apps.shoutit.permissions import PERMISSION_ACTIVATED
from apps.shoutit.templatetags import template_filters
from apps.shoutit.tiers import RESPONSE_RESULT_ERROR_NOT_LOGGED_IN, RESPONSE_RESULT_ERROR_NOT_ACTIVATED, RESPONSE_RESULT_ERROR_REDIRECT, RESPONSE_RESULT_ERROR_BAD_REQUEST, RESPONSE_RESULT_ERROR_404, RESPONSE_RESULT_ERROR_FORBIDDEN, RESPONSE_RESULT_ERROR_PERMISSION_NEEDED
from apps.shoutit.utils import shout_link
from apps.shoutit.xhr_utils import xhr_respond, redirect_to_modal_xhr
from apps.shoutit.api.api_utils import get_object_url
from apps.shoutit.api.renderers import render_message, render_shout, render_tag, render_currency, render_conversation, render_conversation_full, render_user, render_notification, render_experience, render_post, render_comment
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

    city = request.user.profile.City if request.user.is_authenticated() else DEFAULT_LOCATION['city']
    pre_city = PredefinedCity.objects.get(City=city)

    variables['user_lat'] = pre_city.Latitude
    variables['user_lng'] = pre_city.Longitude
    variables['user_country'] = pre_city.Country
    variables['user_city'] = pre_city.City
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
    elif RESPONSE_RESULT_ERROR_NOT_ACTIVATED in result.errors or (RESPONSE_RESULT_ERROR_PERMISSION_NEEDED in result.errors and PERMISSION_ACTIVATED in result.missing_permissions):
        return redirect_to_modal_xhr(request, '/reactivate/', _("You are not activated yet"), 'reactivate')
    elif RESPONSE_RESULT_ERROR_REDIRECT in result.errors:
        return xhr_respond(code=ENUM_XHR_RESULT.REDIRECT, message=result.messages and result.messages[0][1] or '', data={'link': (result.data and 'next' in result.data and result.data['next']) or (result.data and 'link' in result.data and result.data['link']) or '/'})
    elif RESPONSE_RESULT_ERROR_PERMISSION_NEEDED in result.errors or RESPONSE_RESULT_ERROR_FORBIDDEN in result.errors:
        return xhr_respond(ENUM_XHR_RESULT.FORBIDDEN, result.messages and '\n'.join(unicode(message[1]) for message in result.messages) or '', message_type='error')
    elif RESPONSE_RESULT_ERROR_BAD_REQUEST in result.errors:
        return xhr_respond(ENUM_XHR_RESULT.BAD_REQUEST, result.messages and '\n'.join(unicode(message[1]) for message in result.messages) or bad_request_message, errors=result.form_errors, message_type='error')
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


def index_mobile(request, result, *args, **kwargs):
    result.data['link'] = request.build_absolute_uri(request.get_full_path())
    result.data['content'] = ''
    return page_html(request, result, 'mobile_base.html')


def activate_modal_mobile(request, result, token):
    result.data['link'] = "shoutit.com%s" % '/' + token + '/'
    shout = Trade.objects.GetValidTrades().filter(OwnerUser=request.user).select_related('Item')
    content = ''
    if len(shout):
        content = shout[0].Item.Name
    result.data['content'] = content
    return page_html(request, result, 'mobile_activation.html')


def browse_html(request, result, browse_type, url_encoded_city, browse_category=None):
    if 'redirect_category' in result.data:
        return HttpResponseRedirect('/%s/%s/' % (browse_type, url_encoded_city))
    if 'redirect_city' in result.data:
        redirect_city = '/%s/%s/' % (browse_type, result.data['browse_city_encoded'])
        if browse_category:
            redirect_city += '%s/' % browse_category
        return HttpResponseRedirect(redirect_city)
    profile = None
    page_title = unicode.title(u"%s%s %s" % (result.data['browse_city'], (" %s" % browse_category) if browse_category else '',browse_type))
    if not browse_category:
        page_desc = _('Shoutit is a social marketplace where buyers and sellers from %(city)s meet. Post or ask for Cars, Electronics, Properties, Food, or Jobs in %(city)s ')%{'city':result.data['browse_city']}
    else:
        page_desc = _('Shoutit is a social marketplace where buyers and sellers from %(city)s meet. Post or ask about %(category)s in %(city)s.')%{'city':result.data['browse_city'],'category':unicode.title(browse_category)}

    if request.user.is_authenticated():
        profile = user_controller.GetProfile(request.user)
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

    import Image

    if result.data['size']:
        path = '%s_%dx%d.png' % (
            os.path.splitext(result.data['picture'])[0], result.data['size'][0], result.data['size'][0])
    else:
        path = result.data['picture']
    if os.path.exists(path):
        im = Image.open(path)
    else:
        im = Image.open(result.data['picture'])
        if result.data['size']:
            im.thumbnail(result.data['size'], Image.ANTIALIAS)
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


def get_initial_api_result(request, result, *args, **kwargs):
    response = None
    if RESPONSE_RESULT_ERROR_404 in result.errors:
        response = rc.NOT_FOUND
    elif RESPONSE_RESULT_ERROR_FORBIDDEN in result.errors or RESPONSE_RESULT_ERROR_NOT_ACTIVATED in result.errors or RESPONSE_RESULT_ERROR_PERMISSION_NEEDED in result.errors:
        response = rc.FORBIDDEN
        if RESPONSE_RESULT_ERROR_FORBIDDEN in result.errors:
            response['X-SHOUTIT-CAUSE'] = 'forbidden'
        elif RESPONSE_RESULT_ERROR_NOT_ACTIVATED in result.errors:
            response['X-SHOUTIT-CAUSE'] = 'not-activated'
        elif RESPONSE_RESULT_ERROR_PERMISSION_NEEDED in result.errors:
            response['X-SHOUTIT-CAUSE'] = 'permission-needed'
        response.status_code = 403
    elif RESPONSE_RESULT_ERROR_BAD_REQUEST in result.errors:
        response = rc.BAD_REQUEST
    elif RESPONSE_RESULT_ERROR_NOT_LOGGED_IN in result.errors:
        response = rc.FORBIDDEN
        response['X-SHOUTIT-CAUSE'] = 'not-logged-in'
    elif not result.errors:
        if request.method == 'POST':
            response = rc.CREATED
        elif request.method == 'DELETE':
            response = rc.DELETED
        else:
            response = rc.ALL_OK

    # needs to be dumped before returned with json.dumps in the called function
    pre_json_result = {
        'api_messages': [{'type': error[0], 'message': unicode(error[1])} for error in result.messages],
        'api_errors': [{'key': k, 'messages': v} for k, v in result.form_errors.iteritems()]
    }

    response['content-type'] = 'application/json'
    return response, pre_json_result


def operation_api(request, result, *args, **kwargs):
    response, pre_json_result = get_initial_api_result(request, result, *args, **kwargs)

    if not result.errors and 'url' in result.data:
        pre_json_result['url'] = result.data['url']

    return response, pre_json_result


def reply_message_api_render(request, result, *args, **kwargs):
    response, pre_json_result = get_initial_api_result(request, result, *args, **kwargs)

    if not result.errors:
        pre_json_result.update({
            'message': render_message(result.data['message'])
        })

    return response, pre_json_result


def shouts_api(request, result, *args, **kwargs):
    response, pre_json_result = get_initial_api_result(request, result, *args, **kwargs)

    if not result.errors:
        shouts = [render_shout(shout) for shout in result.data['shouts']]

        pre_json_result.update({
            'shouts_count': len(shouts),
            'shouts': shouts
        })

        if 'pages_count' in result.data:
            pre_json_result['pages_count'] = result.data['pages_count']

        if 'is_last_page' in result.data:
            pre_json_result['is_last_page'] = result.data['is_last_page']

        if 'city' in result.data:
            pre_json_result['city'] = result.data['city']

    return response, pre_json_result


def tags_api(request, result, *args, **kwargs):
    response, pre_json_result = get_initial_api_result(request, result, *args, **kwargs)

    if not result.errors:
        tags = [render_tag(tag) for tag in result.data]
        pre_json_result.update({
            'count': len(tags),
            'tags': tags
        })

    return response, pre_json_result


def currencies_api(request, result, *args, **kwargs):
    response, pre_json_result = get_initial_api_result(request, result, *args, **kwargs)

    if not result.errors:
        currencies = [render_currency(currency) for currency in result.data['currencies']]
        pre_json_result.update({
            'count': len(currencies),
            'currencies': currencies
        })

    return response, pre_json_result


def shout_api(request, result, *args, **kwargs):
    response, pre_json_result = get_initial_api_result(request, result, *args, **kwargs)

    if not result.errors:
        shouts = [render_shout(shout) for shout in result.data['shouts']]
        shout = render_shout(result.data['shout'])
        if 'conversations' in result.data:
            shout.update({'conversations': [render_conversation(conversation) for conversation in result.data['conversations']]})

        if 'conversation' in result.data:
            shout.update({'conversation': render_conversation_full(result.data['conversation'])})

        pre_json_result.update({
            'count': len(shouts),
            'shout': shout,
            'shouts': shouts
        })

    return response, pre_json_result


def shout_brief_api(request, result, *args, **kwargs):
    response, pre_json_result = get_initial_api_result(request, result, *args, **kwargs)

    if not result.errors:
        shout = render_shout(result.data['shout'])
        pre_json_result.update({'shout': shout})

    return response, pre_json_result


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


def shout_xhr(request, result, *args, **kwargs):
    response, pre_json_result = get_initial_api_result(request, result, *args, **kwargs)

    if not result.errors:
        shouts = [shout for shout in result.data['shouts']]

        pre_json_result.update({
            'count': len(shouts),
            'shouts': shouts
        })
    else:
        return get_initial_json_response(request, result)

    response = xhr_respond(ENUM_XHR_RESULT.SUCCESS, "", data=pre_json_result)
    return response


def shouts_location_api(request, result, *args, **kwargs):
    response, pre_json_result = get_initial_api_result(request, result, *args, **kwargs)

    if not result.errors:
        pre_json_result['shouts'] = []
        for i in range(len(result.data['shout_pks'])):
            pre_json_result['shouts'].append({
                'id': result.data['shout_pks'][i],
                'location': {
                    'latitude': result.data['locations'][i].split(' ')[0],
                    'longitude': result.data['locations'][i].split(' ')[1],
                },
                'type': PostType.values[result.data['shout_types'][i]],
                'name': result.data['shout_names'][i]
            })
        pre_json_result['count'] = len(pre_json_result['shouts'])

    return response, pre_json_result


def shouts_clusters_api(request, result, *args, **kwargs):
    response, pre_json_result = get_initial_api_result(request, result, *args, **kwargs)

    if not result.errors:
        pre_json_result.update(result.data)

    return response, pre_json_result


def shout_form_renderer_api(request, result, *args, **kwargs):
    response, pre_json_result = get_initial_api_result(request, result, *args, **kwargs)
    if 'shout' in result.data:
        pre_json_result['shout'] = render_shout(result.data['shout'])

    return response, pre_json_result


def tag_api(request, result, *args, **kwargs):
    response, pre_json_result = get_initial_api_result(request, result, *args, **kwargs)

    if not result.errors:
        tag = render_tag(result.data['tag'])

        if 'shouts_count' in result.data:
            tag['shouts_count'] = result.data['shouts_count']

        if 'listeners_count' in result.data:
            tag['listeners_count'] = result.data['listeners_count']

        if 'is_listening' in result.data:
            tag['is_listening'] = result.data['is_listening']

    else:
        tag = None

    pre_json_result['tag'] = tag

    return response, pre_json_result


def user_api(request, result, *args, **kwargs):
    response, pre_json_result = get_initial_api_result(request, result, *args, **kwargs)

    if not result.errors:
        is_owner = 'is_owner' in result.data and result.data['is_owner'] or False
        user = render_user(result.data['profile'].user, level=5, owner=is_owner)

        user['is_owner'] = is_owner

        if 'shouts_count' in result.data:
            user['shouts_count'] = result.data['shouts_count']

        if 'listeners_count' in result.data:
            user['listeners_count'] = result.data['listeners_count']

        if 'listening_count' in result.data:
            user['listening_count'] = result.data['listening_count']

        if 'is_listening' in result.data:
            user['is_listening'] = result.data['is_listening']

    else:
        user = None

    pre_json_result['user'] = user

    return response, pre_json_result


def push_user_api(request, result, *args, **kwargs):
    response, pre_json_result = get_initial_api_result(request, result, *args, **kwargs)

    if not result.errors:
        user = render_user(request.user, level=5, owner=True)

    else:
        user = None

    pre_json_result['user'] = user

    return response, pre_json_result


def user_location(request, result, *args, **kwargs):
    response, pre_json_result = get_initial_api_result(request, result, *args, **kwargs)

    if not result.errors:
        user = render_user(request.user, level=3, owner=True)
    else:
        user = None

    pre_json_result['user'] = user

    return response, pre_json_result


def notifications_api(request, result, *args, **kwargs):
    response, pre_json_result = get_initial_api_result(request, result, *args, **kwargs)

    if not result.errors:
        pre_json_result['notifications'] = [render_notification(notification) for notification in result.data['notifications']]
        pre_json_result['count'] = len(pre_json_result['notifications'])

    return response, pre_json_result


def unread_notifications_api(request, result, *args, **kwargs):
    response, pre_json_result = get_initial_api_result(request, result, *args, **kwargs)

    if not result.errors:
        pre_json_result['notificationsWithouMessages'] = result.data['notificationsWithouMessages']
        pre_json_result['unread_conversations'] = result.data['unread_conversations']

    return response, pre_json_result


def conversations_api(request, result, *args, **kwargs):
    response, pre_json_result = get_initial_api_result(request, result, *args, **kwargs)

    if not result.errors:
        if 'is_last_page' in result.data:
            pre_json_result['is_last_page'] = result.data['is_last_page']
        if 'is_owner' in result.data and result.data['is_owner']:
            pre_json_result['conversations'] = [render_conversation(conversation) for conversation in result.data['conversations']]
        else:
            pre_json_result['conversations'] = [render_conversation_full(conversation) for conversation in result.data['conversations']]
        pre_json_result['count'] = len(pre_json_result['conversations'])

    return response, pre_json_result


def conversation_api(request, result, *args, **kwargs):
    response, pre_json_result = get_initial_api_result(request, result, *args, **kwargs)

    if not result.errors:
        pre_json_result['conversation'] = render_conversation(result.data['conversation'])
        pre_json_result['conversation_messages'] = [render_message(message) for message in result.data['conversation_messages']]

    return response, pre_json_result


def stats_api(request, result, *args, **kwargs):
    response, pre_json_result = get_initial_api_result(request, result, *args, **kwargs)

    if not result.errors:
        if 'listeners' in result.data:
            pre_json_result['listeners'] = [render_user(listener, 2) for listener in result.data['listeners']]

        if 'listening' in result.data:
            pre_json_result['listening'] = {}
            if 'users' in result.data['listening']:
                pre_json_result['listening']['users'] = [render_user(following.user, 2) for following in result.data['listening']['users']]
            if 'tags' in result.data['listening']:
                pre_json_result['listening']['tags'] = [render_tag(tag) for tag in result.data['listening']['tags']]

    return response, pre_json_result


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
        profile = user_controller.GetProfile(user)

        if t and (isinstance(profile, Profile) and not request.user.profile.isSSS) or (isinstance(profile, Business)) or (user.BusinessCreateApplication.count()):
            t.disable()

        link = 'http://' + settings.SHOUT_IT_DOMAIN

        if t.Type == int(constants.TOKEN_TYPE_HTML_EMAIL_BUSINESS_ACTIVATE):
            request.session['business_user_id'] = user.pk
            response = HttpResponseRedirect('/bsignup/')
            response.set_cookie('ba_t_' + request.session.session_key, token)
            return response

        if t.Type == int(constants.TOKEN_TYPE_HTML_EMAIL_BUSINESS_CONFIRM):
            url = link + '/'
            response = HttpResponseRedirect(url + '#confirm_business')
            response.set_cookie('bc_t_' + request.session.session_key, token)
            return response

        shout = Trade.objects.GetValidTrades().filter(OwnerUser=t.user)
        if len(shout):
            url = shout_link(shout[0])
        else:
            url = link + '/'

        if t.Type == int(constants.TOKEN_TYPE_RECOVER_PASSWORD) and request.user.is_authenticated():
            response = HttpResponseRedirect(link + '/user/' + request.user.username + '/#edit')
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
        profile = request.user.is_authenticated() and user_controller.GetProfile(request.user) or None
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
            'html': render_to_string('experiences_stream.html', variables) ,
            'count': len(result.data['experiences'])
        }
        return xhr_respond(ENUM_XHR_RESULT.SUCCESS, '', data=data)
    else:
        return get_initial_json_response(request, result)


def experiences_api(request, result, *args, **kwargs):
    response, pre_json_result = get_initial_api_result(request, result, *args, **kwargs)

    if not result.errors:
        experiences = [render_experience(experience) for experience in result.data['experiences']]

        pre_json_result.update({
            'count': len(experiences),
            'experiences': experiences
        })

        if 'pages_count' in result.data:
            pre_json_result['pages_count'] = result.data['pages_count']

        if 'is_last_page' in result.data:
            pre_json_result['is_last_page'] = result.data['is_last_page']

    return response, pre_json_result


def view_experience_api(request, result, *args, **kwargs):
    response, pre_json_result = get_initial_api_result(request, result, *args, **kwargs)

    if not result.errors:
        experience = render_experience(result.data['experience'])
        if 'timestamp' in result.data:
            pre_json_result['timestamp'] = result.data['timestamp']
        pre_json_result['experience'] = experience

    return response, pre_json_result


def activities_stream_json(request, result):
    if not result.errors:
        variables = {
            'posts': result.data['posts'],
            'constants': constants.post_types,
            'event_types': constants.event_types
        }
        variables = RequestContext(request, variables)
        data = {
            'html': render_to_string('user_home_stream.html', variables),
            'count': len(result.data['posts'])
        }
        return xhr_respond(ENUM_XHR_RESULT.SUCCESS, '', data=data)
    else:
        return get_initial_json_response(request, result)


def activities_api(request, result, *args, **kwargs):
    response, pre_json_result = get_initial_api_result(request, result, *args, **kwargs)

    if not result.errors:
        posts = [render_post(post) for post in result.data['posts']]

        pre_json_result.update({
            'count': len(posts),
            'posts': posts
        })

        if 'pages_count' in result.data:
            pre_json_result['pages_count'] = result.data['pages_count']

        if 'is_last_page' in result.data:
            pre_json_result['is_last_page'] = result.data['is_last_page']

    return response, pre_json_result


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


def gallery_items_stream_json(request, result):
    if not result.errors:
        variables = {
            'items': result.data['items'],
            'IsOwner': result.data['IsOwner']
        }
        variables = RequestContext(request, variables)
        data = {'html': render_to_string('gallery_items_stream.html', variables)}
        return xhr_respond(ENUM_XHR_RESULT.SUCCESS, '', data=data)
    else:
        return get_initial_json_response(request, result)


def post_experience_json_renderer(request, result, message=_('Your experience was post successfully.')):
    if not result.errors:
        data = {
            'text': result.data['experience'].Text,
            'state': int(result.data['experience'].State),
            'date': result.data['experience'].DatePublished.strftime('%d/%m/%Y %H:%M:%S%z'),
            'next': shout_link(result.data['experience'])
        }
        return xhr_respond(ENUM_XHR_RESULT.SUCCESS, message=message , data=data)
    else:
        return get_initial_json_response(request, result)


def comment_on_post_json_renderer(request, result, message=_('Your comment was post successfully.')):
    if not result.errors:
        data = {
            'id': result.data['comment'].pk,
            'text': result.data['comment'].Text,
            'date': result.data['comment'].DateCreated.strftime('%d/%m/%Y %H:%M:%S%z')
        }
        return xhr_respond(ENUM_XHR_RESULT.SUCCESS, message = message , data=data)
    else:
        return get_initial_json_response(request, result)


def profile_json_renderer(request, result):
    if not result.errors:
        data = {
            'users': [
                {
                    'username': user.username,
                    'name': user.name,
                    'category_id': isinstance(user_controller.GetProfile(user), Business) and user.profile.Category.pk or None,
                    'about': user.Bio,
                    'lat': user.Latitude,
                    'lng': user.Longitude,
                    'city': user.City,
                    'country': user.Country,
                    'image': user.Image,
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
                    'image': template_filters.thumbnail(user_controller.GetProfile(user).Image, 32)
                } for user in result.data['users']
            ]
        }

        return xhr_respond(ENUM_XHR_RESULT.SUCCESS, '', data=data)
    else:
        return get_initial_json_response(request, result)


def gallery_item_json_renderer(request, result, message=_('Your item was added successfully.')):
    if not result.errors:
        data = {
            'name': result.data['item'].Name,
            'description': result.data['item'].Description,
            'price': result.data['item'].Price,
            'currency': result.data['item'].Currency.Code,
            'images': [image.Image for image in result.data['item'].GetImages()]
        }
        return xhr_respond(ENUM_XHR_RESULT.SUCCESS, message=message, data=data)
    else:
        return get_initial_json_response(request, result)


def post_comments_json_renderer(request, result):
    if not result.errors:
        data = {
            'comments': [
                {
                    'id': comment.pk,
                    'isOwner': comment.isOwner,
                    'text': comment.Text,
                    'date': comment.DateCreated.strftime('%d/%m/%Y %H:%M:%S%z')
                } for comment in result.data['comments']]
        }
        return xhr_respond(ENUM_XHR_RESULT.SUCCESS, '', data=data)
    else:
        return get_initial_json_response(request, result)


def api_post_comments(request, result, *args, **kwargs):
    response, pre_json_result = get_initial_api_result(request, result, *args, **kwargs)

    if not result.errors:
        comments = [render_comment(comment) for comment in result.data['comments']]

        pre_json_result.update({
            'count': len(comments),
            'timestamp': result.data['timestamp'],
            'comments': comments
        })

    return response, pre_json_result


def live_events_json_renderer(request, result):
    if not result.errors:
        events_arr = []
        for event in result.data['events']:
            variables = {
                'event': event,
                'event_types': constants.event_types
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


def categories_api(request, result):
    def _get_category_dict(category):
        d = {'name': category.Name, 'id': category.pk}
        children = category.children.all().order_by('Name')
        d['children_count'] = len(children)
        if children:
            d['children'] = [_get_category_dict(child) for child in children]
        return d
    response, pre_json_result = get_initial_api_result(request, result)
    if not result.errors:
        if 'categories' in result.data:
            categories = [_get_category_dict(c) for c in result.data['categories']]
        else:
            categories = []
        pre_json_result['categories'] = categories
        pre_json_result['count'] = len(categories)

    return response, pre_json_result


def profiles_api(request, result, *args, **kwargs):
    response, pre_json_result = get_initial_api_result(request, result)

    if not result.errors:
        pre_json_result['users'] = [render_user(user, 2) for user in result.data['users']]

    return response, pre_json_result
