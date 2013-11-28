import math
from django.views.decorators.csrf import csrf_exempt
from django.utils.translation import ugettext_lazy as _
from apps.shoutit.forms import *
from apps.shoutit.models import *
from apps.shoutit.permissions import PERMISSION_ACTIVATED, PERMISSION_SEND_MESSAGE
from apps.shoutit.tiered_views.renderers import *
from apps.shoutit.tiered_views.validators import *
from apps.shoutit.tiers import *
from apps.shoutit.constants import *
from apps.shoutit.controllers import message_controller, shout_controller

@non_cached_view(methods=['GET', 'DELETE'],
	validator=delete_conversation_validator,
	api_renderer=operation_api,
	json_renderer=json_data_renderer)
@refresh_cache(tags=[CACHE_TAG_MESSAGES])
def delete_conversation(request):
	result = ResponseResult()
	id = request.GET[u'id']
	id = Base62ToInt(id)
	message_controller.DeleteConversation(request.user, id)
	#refresh_cache_dynamically([CACHE_TAG_MESSAGES.make_dynamic(request.user)])
	return result

@non_cached_view(methods=['GET', 'DELETE'],
	validator=delete_message_validator,
	api_renderer=operation_api,
	json_renderer=json_data_renderer)
@refresh_cache(tags=[CACHE_TAG_MESSAGES])
def delete_message(request):
	id = request.GET[u'id']
	id = Base62ToInt(id)
	message_controller.DeleteMessage(request.user, id)
	#refresh_cache_dynamically([CACHE_TAG_MESSAGES.make_dynamic(request.user)])
	result = ResponseResult()
	return result

def get_html_message(request):
	if request.GET[u'type'] == "message":
		variables = RequestContext(request, {'message': message_controller.GetMessage(Base62ToInt(request.GET[u'id']))})
		data = {'html': render_to_string("message.html", variables)}
	else:
		variables = RequestContext(request,
				{'conversation': message_controller.GetConversation(Base62ToInt(request.GET[u'id']), request.user)})
		data = {'html': render_to_string("conversation.html", variables)}

	return xhr_respond(ENUM_XHR_RESULT.SUCCESS, '', data=data)

@cached_view(level=CACHE_LEVEL_USER, tags=[CACHE_TAG_MESSAGES],
	methods=['GET'],
	validator=lambda request, shout_id: shout_owner_view_validator(request, Base62ToInt(shout_id)),
	login_required=True,
	api_renderer=conversations_api)
def get_shout_conversations(request, shout_id):
	result = ResponseResult()
	shout_id = Base62ToInt(shout_id)
	shout = shout_controller.GetPost(shout_id, True, True)
	result.data['conversations'] = message_controller.GetShoutConversations(shout_id, request.user)
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
		message = Message.objects.get(pk=Base62ToInt(message_id))
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
		result.data['title'] if result.data.has_key('title') else ''))
@refresh_cache(tags=[CACHE_TAG_MESSAGES])
def read_conversation(request, conversation_id):
	result = ResponseResult()
	result.data['form'] = MessageForm()
	result.data['conversation'] = message_controller.GetConversation(Base62ToInt(conversation_id), request.user)
	result.data['shout'] = result.data['conversation'].AboutPost
	result.data['conversation_messages'] = message_controller.ReadConversation(request.user,
		Base62ToInt(conversation_id))
	result.data['conversation_id'] = Base62ToInt(conversation_id)
	name = result.data['conversation'].With.name()
	name = name if name != '' else result.data['conversation'].With.username
	result.data['title'] = _('You and ') + name

	return result

@non_cached_view(post_login_required=True,
	methods=['GET', 'POST'],
	validator=send_message_validator,
	json_renderer=lambda request, result, shout_id, conversation_id: json_send_message(request, result),
	html_renderer=lambda request, result, shout_id, conversation_id: page_html(request, result, 'send_message.html',
		_('Messages')),
	permissions_required = [PERMISSION_ACTIVATED, PERMISSION_SEND_MESSAGE])
@refresh_cache(tags=[CACHE_TAG_MESSAGES])
def send_message(request, shout_id, conversation_id='0'):
	if not conversation_id:
		conversation_id = '0'
	result = ResponseResult()
	shout = shout_controller.GetPost(utils.Base62ToInt(shout_id))
	to_user = shout.OwnerUser
	result.data['to_user'] = to_user
	if request.method == 'POST':
		permissions_result = permissions_point_cut(request, [PERMISSION_ACTIVATED, PERMISSION_SEND_MESSAGE])
		if permissions_result:
			return permissions_result
		form = MessageForm(request.POST)
		form.is_valid()
		message = message_controller.SendMessage(request.user, to_user, shout, form.cleaned_data['text'],
			conversation_id=Base62ToInt(conversation_id))
		result.data['conversation_id'] = message.Conversation_id
		result.data['message'] = message
		#refresh_cache_dynamically([CACHE_TAG_MESSAGES.make_dynamic(message.Conversation.FromUser), CACHE_TAG_MESSAGES.make_dynamic(message.Conversation.ToUser)])
	else:
		if request.user.is_authenticated():
			conversation = message_controller.ConversationExist(request.user, shout.OwnerUser, shout)
			if conversation:
				result.errors.append(RESPONSE_RESULT_ERROR_REDIRECT)
				result.data['next'] = '/messages/%s/#send_message_form' % IntToBase62(conversation.pk)
				return result
		form = MessageForm()

	result.data['form'] = form
	result.data['shout'] = shout
	return result

@non_cached_view(login_required=True, methods=['POST'],
	api_renderer=reply_message_api_render,
	validator=read_conversation_validator)
@refresh_cache(tags=[CACHE_TAG_MESSAGES])
def reply_to_conversation(request, conversation_id):
	result = ResponseResult()
	conversation = message_controller.GetConversation(Base62ToInt(conversation_id), request.user)
	msg = message_controller.SendMessage(request.user, conversation.With, conversation.AboutPost, request.POST['text'],
		conversation.pk)
	#refresh_cache_dynamically([CACHE_TAG_MESSAGES.make_dynamic(conversation.FromUser), CACHE_TAG_MESSAGES.make_dynamic(conversation.ToUser)])
	result.data['message'] = msg
	result.messages.append(('success', _('Your message was sent successfully.')))
	return result

@non_cached_view(login_required=True, methods=['POST'],
	validator=lambda request, shout_id, *args, **kwargs: object_exists_validator(shout_controller.GetPost,
		_('Shout does not exist.'), utils.Base62ToInt(shout_id)),
	api_renderer=reply_message_api_render)
@refresh_cache(tags=[CACHE_TAG_MESSAGES])
def reply_to_shout(request, shout_id):
	result = ResponseResult()
	shout = shout_controller.GetPost(Base62ToInt(shout_id))
	conversation = message_controller.ConversationExist(request.user, shout.OwnerUser, shout)
	if conversation:
		message = message_controller.SendMessage(request.user, shout.OwnerUser, shout, request.POST['text'],
			conversation.pk)
	else:
		message = message_controller.SendMessage(request.user, shout.OwnerUser, shout, request.POST['text'])
		conversation = message_controller.ConversationExist(request.user, shout.OwnerUser, shout)
	#refresh_cache_dynamically([CACHE_TAG_MESSAGES.make_dynamic(conversation.FromUser), CACHE_TAG_MESSAGES.make_dynamic(conversation.ToUser)])
	result.messages.append(('success', _('Your message was sent successfully.')))
	result.data['url'] = get_object_url(message.Conversation)
	result.data['message'] = message
	return result

@cached_view(tags=[CACHE_TAG_MESSAGES],
	methods=['GET'],
	login_required=True,
	api_renderer=conversations_api,
	json_renderer=lambda request, result, username, *args: read_conversations_stream_json(request, result))
@refresh_cache(tags=[CACHE_TAG_MESSAGES])
def read_conversations_stream(request, page_num=None):
	if not page_num:
		page_num = 1
	else:
		page_num = int(page_num)
	result = ResponseResult()
	#conversations_count = get_data([CACHE_TAG_MESSAGES.make_dynamic(request.user)], message_controller.ConversationsCount, request.user)
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
	#result.data['conversations'] = get_data([CACHE_TAG_MESSAGES.make_dynamic(request.user)], message_controller.ReadConversations, request.user, 0, DEFAULT_PAGE_SIZE)
	result.data['conversations'] = message_controller.ReadConversations(request.user, 0, DEFAULT_PAGE_SIZE)
	return result