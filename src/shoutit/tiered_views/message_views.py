import math
import time

from django.http import Http404
from django.template import RequestContext
from django.template.loader import render_to_string
from django.views.decorators.csrf import csrf_exempt
from django.utils.translation import ugettext_lazy as _

from shoutit.models import Message
from shoutit.permissions import PERMISSION_ACTIVATED, PERMISSION_SEND_MESSAGE
from shoutit.tiered_views.renderers import json_data_renderer, json_renderer, conversation_json, \
    page_html, json_send_message, read_conversations_stream_json
from shoutit.tiered_views.validators import *
from shoutit.tiers import *
from common.constants import *
from shoutit.controllers import shout_controller, message_controller
from shoutit.xhr_utils import xhr_respond


@non_cached_view(methods=['GET', 'DELETE'], login_required=True,
                 validator=delete_conversation_validator,
                 json_renderer=json_data_renderer)
def delete_conversation(request, conversation_id):
    result = ResponseResult()
    conversation = request.validation_result.data
    message_controller.hide_conversation_from_user(conversation, request.user)
    return result


@non_cached_view(methods=['GET', 'DELETE'], login_required=True,
                 validator=delete_message_validator,
                 json_renderer=json_data_renderer)
def delete_message(request, conversation_id, message_id):
    result = ResponseResult()
    message = request.validation_result.data
    message_controller.hide_message_from_user(message, request.user)
    return result


def get_html_message(request):
    if request.GET[u'type'] == "message":
        variables = RequestContext(request, {'message': message_controller.get_message(request.GET[u'id'])})
        data = {'html': render_to_string("message.html", variables)}
    else:
        variables = RequestContext(request, {'conversation': message_controller.get_conversation(request.GET[u'id'], request.user)})
        data = {'html': render_to_string("conversation.html", variables)}

    return xhr_respond(ENUM_XHR_RESULT.SUCCESS, '', data=data)


@non_cached_view(methods=['GET'], login_required=True, validator=lambda request, shout_id: shout_owner_view_validator(request, shout_id))
def get_shout_conversations(request, shout_id):
    result = ResponseResult()
    shout = shout_controller.get_post(shout_id, True, True)
    result.data['conversations'] = message_controller.get_shout_conversations(shout_id, request.user)
    result.data['is_owner'] = (request.user.pk == shout.user.pk)
    return result


@csrf_exempt
@non_cached_view(json_renderer=json_renderer,
                 methods=['POST'],
                 login_required=True)
def mark_message_as_read(request, message_id):
    result = ResponseResult()
    try:
        message = Message.objects.get(pk=message_id)
        message.is_read = True
        message.save()
    except ObjectDoesNotExist:
        raise Http404()
    return result


@non_cached_view(login_required=True,
                 methods=['GET'],
                 validator=read_conversation_validator,
                 json_renderer=lambda request, result, conversation_id: conversation_json(request, result),
                 html_renderer=lambda request, result, conversation_id: page_html(request, result, 'conversations.html',
                                                                                  'title' in result.data and result.data['title'] or ''))
def read_conversation(request, conversation_id):
    result = ResponseResult()
    conversation = request.validation_result.data['conversation']
    result.data['form'] = MessageForm()
    result.data['conversation'] = conversation
    result.data['shout'] = conversation.AboutPost
    result.data['conversation_messages'] = message_controller.ReadConversation(request.user, conversation_id)
    result.data['conversation_id'] = conversation_id
    name = result.data['conversation'].With.name
    name = name if name != '' else conversation.With.username
    result.data['title'] = _('You and ') + name

    return result


@non_cached_view(methods=['GET', 'POST'], post_login_required=True, validator=send_message_validator,
                 json_renderer=lambda request, result, shout_id, conversation_id: json_send_message(request, result),
                 html_renderer=lambda request, result, shout_id, conversation_id: page_html(request, result, 'send_message.html',
                                                                                            _('Messages')),
                 permissions_required=[PERMISSION_ACTIVATED, PERMISSION_SEND_MESSAGE])
def send_message(request, shout_id, conversation_id=None):
    result = ResponseResult()
    validation_result = request.validation_result

    shout = validation_result.data['shout']
    conversation = validation_result.data['conversation']
    to_user = conversation.With if conversation else shout.user

    result.data['to_user'] = to_user
    if request.method == 'POST':
        form = MessageForm(request.POST)
        form.is_valid()
        message = message_controller.send_message(request.user, to_user, shout, form.cleaned_data['text'], conversation=conversation)
        result.data['conversation_id'] = message.Conversation_id
        result.data['message'] = message
    else:
        if request.user.is_authenticated() and conversation:
            result.errors.append(RESPONSE_RESULT_ERROR_REDIRECT)
            result.data['next'] = '/messages/%s/#send_message_form' % conversation.pk
            return result
        form = MessageForm()

    result.data['form'] = form
    result.data['shout'] = shout
    return result


@non_cached_view(login_required=True, methods=['POST'], validator=reply_in_conversation_validator)
def reply_in_conversation(request, conversation_id):
    """Reply in a Conversation."""
    result = ResponseResult()
    validation_result = request.validation_result

    conversation = validation_result.data['conversation']
    text = validation_result.data['text']
    attachments = validation_result.data['attachments']

    message = message_controller.send_message(request.user, conversation.With, conversation.AboutPost, text, conversation=conversation)

    result.data['message'] = message
    result.messages.append(('success', _('Your message was sent successfully.')))
    return result


@non_cached_view(methods=['GET'], login_required=True,
                 json_renderer=lambda request, result, *args, **kwargs: read_conversations_stream_json(request, result))
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


@non_cached_view(methods=['GET'], login_required=True,
                 html_renderer=lambda request, result: page_html(request, result, 'conversations.html', _('Messages')))
def read_conversations(request):
    result = ResponseResult()
    result.data['conversations'] = message_controller.ReadConversations(request.user, 0, DEFAULT_PAGE_SIZE)
    return result
