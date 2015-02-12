from django.views.decorators.vary import vary_on_headers

from .handler import typemapper
from .authentication import NoAuthentication

CHALLENGE = object()


class Resource(object):
    """
    Resource. Create one for your URL mappings, just
    like you would with Django. Takes one argument,
    the handler. The second argument is optional, and
    is an authentication handler. If not specified,
    `NoAuthentication` will be used by default.
    """
    callmap = {'GET': 'read', 'POST': 'create',
               'PUT': 'update', 'DELETE': 'delete'}

    def __init__(self, handler, authentication=None):
        if not callable(handler):
            raise AttributeError("Handler not callable.")

        self.handler = handler()
        self.csrf_exempt = getattr(self.handler, 'csrf_exempt', True)

        if not authentication:
            self.authentication = (NoAuthentication(),)
        elif isinstance(authentication, (list, tuple)):
            self.authentication = authentication
        else:
            self.authentication = (authentication,)

    @property
    def anonymous(self):
        """
        Gets the anonymous handler. Also tries to grab a class
        if the `anonymous` value is a string, so that we can define
        anonymous handlers that aren't defined yet (like, when
        you're subclassing your basehandler into an anonymous one.)
        """
        if hasattr(self.handler, 'anonymous'):
            anon = self.handler.anonymous

            if callable(anon):
                return anon

            for klass in typemapper.keys():
                if anon == klass.__name__:
                    return klass

        return None

    def authenticate(self, request, rm):
        actor, anonymous = False, True

        for authenticator in self.authentication:
            if not authenticator.is_authenticated(request):
                if self.anonymous and rm in self.anonymous.allowed_methods:

                    actor, anonymous = self.anonymous(), True
                else:
                    actor, anonymous = authenticator.challenge, CHALLENGE
            else:
                return self.handler, self.handler.is_anonymous

        return actor, anonymous

    @vary_on_headers('Authorization')
    def __call__(self, request, *args, **kwargs):
        raise NotImplementedError()



