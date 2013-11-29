from importlib import import_module
import apps.shoutit.settings as settings
from apps.shoutit.controllers import realtime_controller, user_controller
from apps.shoutit.controllers import notifications_controller
from apps.shoutit.controllers import message_controller
from apps.shoutit.forms import *
from apps.shoutit.models import *
from apps.shoutit.tiered_views.renderers import *
from apps.shoutit.tiered_views.validators import *
from apps.shoutit.tiers import *
from apps.shoutit.constants import *

@non_cached_view(api_renderer=operation_api,
	methods=['POST'])
def add_apns_token(request, token):
	from common.tagged_cache import TaggedCache

	apns_tokens = TaggedCache.get('apns|%s' % request.user.username)
	if not apns_tokens:
		apns_tokens = []
	if token not in apns_tokens:
		apns_tokens.append(token)
		TaggedCache.set('apns|%s' % request.user.username, apns_tokens)
	return ResponseResult()

@non_cached_view(api_renderer=operation_api,
	methods=['DELETE'])
def remove_apns_token(request, token):
	from common.tagged_cache import TaggedCache

	apns_tokens = TaggedCache.get('apns|%s' % request.user.username)
	if apns_tokens:
		apns_tokens.remove(token)
		TaggedCache.set('apns|%s' % request.user.username, apns_tokens)
	return ResponseResult()

def get_session_data(request, session_key=None):
	from django.contrib.auth import SESSION_KEY

	engine = import_module(settings.SESSION_ENGINE)
	if session_key:
		if engine.SessionStore().exists(session_key):
			session = engine.SessionStore(session_key)
			if session.get_expiry_age() <= 0:
				raise Http404()
		else:
			raise Http404()
	else:
		is_radis = False
		old_session = None
		r = None
		try:
			import redis

			is_radis = True
			r = redis.Redis(host=settings.SESSION_REDIS_HOST, port=settings.SESSION_REDIS_PORT,
				socket_timeout=settings.REDIS_SOCKET_TIMEOUT)
			if request.user.is_authenticated():
				old_session = r.get('usersession:%d' % request.user.id)
		except ImportError:
			pass
		if old_session:
			session = engine.SessionStore(old_session)
			if not session._session:
				session[SESSION_KEY] = request.user.id
				session.save()
				r.setnx('usersession:%d' % request.user.id, session._get_session_key())
		else:
			session = engine.SessionStore()
			if request.user.is_authenticated():
				session[SESSION_KEY] = request.user.id
			session.save()
			if is_radis and request.user.is_authenticated():
				r.setnx('usersession:%d' % request.user.id, session._get_session_key())
	try:
		result = {}
		if session.has_key(SESSION_KEY):
			result.update(render_user(User.objects.get(pk=session[SESSION_KEY])))
		result['session_key'] = session._get_session_key()
		result = json.dumps(result)
	except:
		raise Http404()
	return HttpResponse(content=result, content_type='text/plain;charset=utf-8')

@non_cached_view(json_renderer=json_renderer,
	api_renderer=operation_api,
	methods=['POST'],
	login_required=True)
@refresh_cache(tags=[CACHE_TAG_NOTIFICATIONS])
def mark_notification_as_read(request, notification_id):
	result = ResponseResult()
	try:
		notification = Notification.objects.get(pk=Base62ToInt(notification_id))
		notification.IsRead = True
		notification.save()
	except ObjectDoesNotExist:
		raise Http404()
	return result

@non_cached_view(json_renderer=json_renderer,
	api_renderer=operation_api,
	methods=['POST'],
	login_required=True)
@refresh_cache(tags=[CACHE_TAG_NOTIFICATIONS])
def mark_notification_as_unread(request, notification_id):
	result = ResponseResult()
	try:
		notification = Notification.objects.get(pk=Base62ToInt(notification_id))
		notification.IsRead = False
		notification.save()
	except ObjectDoesNotExist:
		raise Http404()
	return result

@cached_view(tags=[CACHE_TAG_NOTIFICATIONS],
	html_renderer=notifications_html,
	json_renderer=notifications_json,
	api_renderer=notifications_api,
	methods=['GET'],
	login_required=True)
def notifications(request):
	result = ResponseResult()
	profile = user_controller.GetProfile(request.user)
	if request.is_ajax() or (hasattr(request, 'is_api') and request.is_api):
		result.data['notifications'] = user_controller.GetNotifications(profile)
	else:
		result.data['notifications'] = user_controller.GetAllNotifications(profile)

	notifications_controller.MarkAllAsRead(request.user)
	return result

@cached_view(tags=[CACHE_TAG_NOTIFICATIONS],
	json_renderer=lambda request, result: json_renderer(request, result, success_message='', data=result.data),
	api_renderer=unread_notifications_api,
	methods=['GET'], login_required=True)
def unread_notifications_count(request):
	result = ResponseResult()
	#	result.data['count'] = request.user.Profile.GetUnreadNotificatiosCount()
	result.data['count'] = user_controller.GetUnreadNotificatiosCount(user_controller.GetProfile(request.user))
	result.data['notificationsWithouMessages'] = notifications_controller.GetUserNotificationsWithoutMessagesCount(
		request.user)
	result.data['unread_conversations'] = message_controller.UnReadConversationsCount(request.user)
	return result

@cached_view(tags=[CACHE_TAG_NOTIFICATIONS],
	json_renderer=notifications_json,
	api_renderer=notifications_api,
	methods=['GET'],
	login_required=True)
def notifications_all(request):
	result = ResponseResult()
	result.data['notifications'] = user_controller.GetAllNotifications(request.user.Profile)
	notifications_controller.MarkAllAsRead(request.user)
	return result

num = 0

def send_fake_notification(request, username):
	global num
	notification = Notification()
	notification.id = num
	num += 1
	notification.ToUser = User.objects.get(username__iexact=username)
	notification.FromUser = User.objects.get(username__iexact='syron')
	notification.Type = NOTIFICATION_TYPE_FOLLOWSHIP
	notification.DateCreated = datetime.now()
	notification.IsRead = False
	notification.AttachedObject = notification.FromUser
	realtime_controller.SendNotification(notification, username)
	return HttpResponse(content='Num: %d' % (num - 1,))