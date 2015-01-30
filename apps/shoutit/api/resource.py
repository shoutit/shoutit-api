from django.http import Http404, HttpResponseNotAllowed, HttpResponseBadRequest

from django.views.decorators.vary import vary_on_headers

from piston3.resource import Resource, CHALLENGE
from piston3.utils import coerce_put_post


class TieredResource(Resource):
    def __init__(self, handler, authentication=None, methods_map=None):
        if not methods_map:
            methods_map = {}
        super(TieredResource, self).__init__(handler, authentication)
        self.csrf_exempt = getattr(self.handler, 'csrf_exempt', True)
        self.handler.methods_map = methods_map
        self.handler.allowed_methods = methods_map.keys()

    @vary_on_headers('Authorization')
    def __call__(self, request, *args, **kwargs):
        """
        for more details about this override, check the main method. in shoutit we kept what we need only.
        """
        rm = request.method.upper()
        if rm == "PUT":
            coerce_put_post(request)

        actor, anonymous = self.authenticate(request, rm)

        if anonymous is CHALLENGE:
            return actor()
        else:
            handler = actor

        if rm not in handler.allowed_methods:
            return HttpResponseNotAllowed(handler.allowed_methods)

        method = getattr(handler, self.callmap.get(rm, ''), None)
        if not method:
            raise Http404

        request = self.cleanup_request(request)

        return method(request, *args, **kwargs)


class MethodDependentAuthentication(object):
    # Example
    # MethodDependentAuthentication({'GET': no_oauth, 'POST': oauth, 'DELETE': oauth})
    def __init__(self, methods_auth_map=None, default=None):
        if not methods_auth_map:
            methods_auth_map = {}
        self.methods_auth_map = methods_auth_map
        self.default = default
        self.last_request = None

    def is_authenticated(self, request):
        self.last_request = request
        if request.method in self.methods_auth_map.keys():
            return self.methods_auth_map[request.method].is_authenticated(request)
        elif self.default:
            return self.default(request)
        else:
            return False

    def challenge(self):
        if self.last_request.method in self.methods_auth_map.keys():
            return self.methods_auth_map[self.last_request.method].challenge()
        elif self.default and hasattr(self.default, 'challenge'):
            return self.default.challenge()
        else:
            return None