import math
from django.template import RequestContext
from django.template.loader import render_to_string
from django.views.decorators.csrf import csrf_exempt
from django.utils.translation import ugettext_lazy as _
from apps.shoutit.api.api_utils import get_object_url
from apps.shoutit.models import Message
from apps.shoutit.permissions import PERMISSION_ACTIVATED, PERMISSION_SEND_MESSAGE
from apps.shoutit.tiered_views.renderers import operation_api, json_data_renderer, conversations_api, json_renderer, conversation_json, \
    page_html, conversation_api, json_send_message, reply_message_api_render, read_conversations_stream_json
from apps.shoutit.tiered_views.validators import *
from apps.shoutit.tiers import *
from apps.shoutit.constants import *
from apps.shoutit.controllers import message_controller, shout_controller
from apps.shoutit.utils import int_to_base62
from apps.shoutit.xhr_utils import xhr_respond


@non_cached_view(methods=['GET', 'DELETE'],
                 validator=delete_conversation_validator,
                 api_renderer=operation_api,
                 json_renderer=json_data_renderer)
@refresh_cache(tags=[CACHE_TAG_MESSAGES])
def delete_conversation(request):
    result = ResponseResult()
    id = request.GET[u'id']
    id = base62_to_int(id)
    message_controller.DeleteConversation(request.user, id)
    return result


@non_cached_view(methods=['GET', 'DELETE'],
                 validator=delete_message_validator,
                 api_renderer=operation_api,
                 json_renderer=json_data_renderer)
@refresh_cache(tags=[CACHE_TAG_MESSAGES])
def delete_message(request):
    id = request.GET[u'id']
    id = base62_to_int(id)
    message_controller.DeleteMessage(request.user, id)
    result = ResponseResult()
    return result


def get_html_message(request):
    if request.GET[u'type'] == "message":
        variables = RequestContext(request, {'message': message_controller.GetMessage(base62_to_int(request.GET[u'id']))})
        data = {'html': render_to_string("message.html", variables)}
    else:
        variables = RequestContext(request, {'conversation': message_controller.get_conversation(base62_to_int(request.GET[u'id']),
                                                                                                 request.user)})
        data = {'html': render_to_string("conversation.html", variables)}

    return xhr_respond(ENUM_XHR_RESULT.SUCCESS, '', data=data)


@cached_view(level=CACHE_LEVEL_USER, tags=[CACHE_TAG_MESSAGES],
             methods=['GET'],
             validator=lambda request, shout_id: shout_owner_view_validator(request, base62_to_int(shout_id)),
             login_required=True,
             api_renderer=conversations_api)
def get_shout_conversations(request, shout_id):
    result = ResponseResult()
    shout_id = base62_to_int(shout_id)
    shout = shout_controller.GetPost(shout_id, True, True)
    result.data['conversations'] = message_controller.get_shout_conversations(shout_id, request.user)
    result.data['is_owner'] = (request.user.pk == shout.OwnerUser.pk)
    return result


@non_cached_view(json_renderer=json_renderer,
                 api_renderer=operation_api,
                 methods=['POST'],
                 login_required=True)
@refresh_cache(tags=[CACHE_TAG_MESSAGES])
@csrf_exempt
def mark_message_as_read(request, message_id):
    result = ResponseResult()
    try:
        message = Message.objects.get(pk=base62_to_int(message_id))
        message.IsRead = True
        message.save()
    except ObjectDoesNotExist:
        raise Http404()
    return result


@non_cached_view(login_required=True,
                 methods=['GET'],
                 api_renderer=conversation_api,
                 validator=read_conversation_validator,
                 json_renderer=lambda request, result, conversation_id: conversation_json(request, result),
                 html_renderer=lambda request, result, conversation_id: page_html(request, result, 'conversations.html',
                                                                                  'title' in result.data and result.data['title'] or ''))
@refresh_cache(tags=[CACHE_TAG_MESSAGES])
def read_conversation(request, conversation_id):
    result = ResponseResult()
    result.data['form'] = MessageForm()
    result.data['conversation'] = message_controller.get_conversation(base62_to_int(conversation_id), request.user)
    result.data['shout'] = result.data['conversation'].AboutPost
    result.data['conversation_messages'] = message_controller.ReadConversation(request.user, base62_to_int(conversation_id))
    result.data['conversation_id'] = base62_to_int(conversation_id)
    name = result.data['conversation'].With.name()
    name = name if name != '' else result.data['conversation'].With.username
    result.data['title'] = _('You and ') + name

    return result


@non_cached_view(post_login_required=True,
                 methods=['GET', 'POST'],
                 validator=send_message_validator,
                 json_renderer=lambda request, result, shout_id, conversation_id: json_send_message(request, result),
                 html_renderer=lambda request, result, shout_id, conversation_id: page_html(request, result, 'send_message.html', _('Messages')),
                 permissions_required=[PERMISSION_ACTIVATED, PERMISSION_SEND_MESSAGE])
@refresh_cache(tags=[CACHE_TAG_MESSAGES])
def send_message(request, shout_id, conversation_id=None):
    result = ResponseResult()
    validation_result = request.validation_result

    shout = validation_result.data['shout']
    conversation = validation_result.data['conversation']
    to_user = conversation.With if conversation else shout.OwnerUser

    result.data['to_user'] = to_user
    if request.method == 'POST':
        permissions_result = permissions_point_cut(request, [PERMISSION_ACTIVATED, PERMISSION_SEND_MESSAGE])
        if permissions_result:
            return permissions_result
        form = MessageForm(request.POST)
        form.is_valid()
        message = message_controller.send_message(request.user, to_user, shout, form.cleaned_data['text'], conversation=conversation)
        result.data['conversation_id'] = message.Conversation_id
        result.data['message'] = message
    else:
        if request.user.is_authenticated() and conversation:
            result.errors.append(RESPONSE_RESULT_ERROR_REDIRECT)
            result.data['next'] = '/messages/%s/#send_message_form' % int_to_base62(conversation.pk)
            return result
        form = MessageForm()

    result.data['form'] = form
    result.data['shout'] = shout
    return result


@non_cached_view(login_required=True, methods=['POST'], validator=reply_in_conversation_validator, api_renderer=reply_message_api_render)
@refresh_cache(tags=[CACHE_TAG_MESSAGES])
def reply_in_conversation(request, conversation_id):
    """Reply in a Conversation."""
    result = ResponseResult()
    validation_result = request.validation_result

    conversation = validation_result.data['conversation']
    text = validation_result.data['text']
    attachments = validation_result.data['attachments']

    message = message_controller.send_message(request.user, conversation.With, conversation.AboutPost, text, conversation=conversation,
                                              attachments=attachments)

    result.data['message'] = message
    result.messages.append(('success', _('Your message was sent successfully.')))
    return result


@non_cached_view(login_required=True, methods=['POST'], validator=reply_to_shout_validator, api_renderer=reply_message_api_render)
@refresh_cache(tags=[CACHE_TAG_MESSAGES])
def reply_to_shout(request, shout_id):
    """Reply to a Shout for first time. request.user shouldn't be the shout owner."""
    result = ResponseResult()
    validation_result = request.validation_result

    shout = validation_result.data['shout']
    text = validation_result.data['text']
    attachments = validation_result.data['attachments']

    message = message_controller.send_message(request.user, shout.OwnerUser, shout, text, attachments=attachments)

    result.messages.append(('success', _('Your message was sent successfully.')))
    result.data['url'] = get_object_url(message.Conversation)
    result.data['message'] = message
    return result


@cached_view(tags=[CACHE_TAG_MESSAGES],
             methods=['GET'],
             login_required=True,
             api_renderer=conversations_api,
             json_renderer=lambda request, result, *args, **kwargs: read_conversations_stream_json(request, result))
@refresh_cache(tags=[CACHE_TAG_MESSAGES])
def read_conversations_stream(request):

    result = ResponseResult()

    page_num = int(request.GET.get('page', 1))
    conversations_count = message_controller.ConversationsCount(request.user)
    result.data['pages_count'] = int(math.ceil(conversations_count / float(DEFAULT_PAGE_SIZE)))
    result.data['conversations'] = message_controller.ReadConversations(request.user, DEFAULT_PAGE_SIZE * (page_num - 1),
                                                                        DEFAULT_PAGE_SIZE * page_num)
    result.data['is_last_page'] = page_num >= result.data['pages_count']
    result.data['is_owner'] = True
    return result


@cached_view(tags=[CACHE_TAG_MESSAGES],
             login_required=True,
             methods=['GET'],
             html_renderer=lambda request, result: page_html(request, result, 'conversations.html', _('Messages')))
@refresh_cache(tags=[CACHE_TAG_MESSAGES])
def read_conversations(request):
    result = ResponseResult()
    result.data['conversations'] = message_controller.ReadConversations(request.user, 0, DEFAULT_PAGE_SIZE)
    return result