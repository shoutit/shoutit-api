from piston.authentication.oauth.utils import get_oauth_request
from psycopg2._psycopg import DatabaseError

from apps.ActivityLogger.models import Request

class ActivityLogger(object):
	def process_response(self, request, response):
		if hasattr(request, 'request_object'):
			return response

		r = Request()
		if request.META.has_key('HTTP_X_REAL_IP'):
			r.ip_address = request.META['HTTP_X_REAL_IP']
		else:
			r.ip_address = request.META['REMOTE_ADDR']
		if getattr(request, 'user', None) and request.user.is_authenticated():
			r.user = request.user
		r.method = request.method
		if request.META.has_key('HTTP_REFERER'):
			r.referer = request.META['HTTP_REFERER']
		r.url = request.build_absolute_uri()
		r.plain_url = request.path
		if request.META.has_key('HTTP_USER_AGENT'):
			r.user_agent = request.META['HTTP_USER_AGENT']
		if getattr(request, 'session', None):
			r.session_id = str(request.session.session_key)
		r.is_ajax = request.is_ajax()
		r.is_api = getattr(request, 'is_api', False)
		if r.is_api:
			try:
				oauth_request = get_oauth_request(request)
				if oauth_request.has_key('oauth_token'):
					from piston.authentication.oauth.store import store
					r.token = store.get_access_token(request, oauth_request, None, oauth_request['oauth_token'])
			except:
				pass
		try:
			r.save()
		except BaseException, e:
			pass

		request.request_object = r
		return response
