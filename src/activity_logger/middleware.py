from piston3.authentication import initialize_server_request

from activity_logger.models import Request


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
                oauth_server, oauth_request = initialize_server_request(request)
                r.token = oauth_server.fetch_access_token(oauth_request)
            except Exception, e:
                print e.message
        try:
            r.save()
        except Exception, e:
            print e.message
            pass

        request.request_object = r
        return response
