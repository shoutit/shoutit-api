from six import add_metaclass

import warnings

from .utils import rc
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from django.conf import settings

typemapper = {}
handler_tracker = []


class HandlerMetaClass(type):
    """
    Metaclass that keeps a registry of class -> handler
    mappings.
    """

    def __new__(cls, name, bases, attrs):
        new_cls = type.__new__(cls, name, bases, attrs)

        def already_registered(model, anon):
            for k, (m, a) in typemapper.items():
                if model == m and anon == a:
                    return k

        if hasattr(new_cls, 'model'):
            if already_registered(new_cls.model, new_cls.is_anonymous):
                if not getattr(settings, 'PISTON_IGNORE_DUPE_MODELS', False):
                    warnings.warn("Handler already registered for model %s, "
                                  "you may experience inconsistent results." % new_cls.model.__name__)

            typemapper[new_cls] = (new_cls.model, new_cls.is_anonymous)
        else:
            typemapper[new_cls] = (None, new_cls.is_anonymous)

        if name not in ('BaseHandler', 'AnonymousBaseHandler'):
            handler_tracker.append(new_cls)

        return new_cls


@add_metaclass(HandlerMetaClass)
class BaseHandler(object):
    """
    Basehandler that gives you CRUD for free.
    You are supposed to subclass this for specific
    functionality.

    All CRUD methods (`read`/`update`/`create`/`delete`)
    receive a request as the first argument from the
    resource. Use this for checking `request.user`, etc.
    """

    anonymous = is_anonymous = False
    allowed_methods = ('GET', 'POST', 'PUT', 'DELETE')

    def read(self, request, *args, **kwargs):
        raise NotImplementedError()

    def create(self, request, *args, **kwargs):
        raise NotImplementedError()

    def update(self, request, *args, **kwargs):
        raise NotImplementedError()

    def delete(self, request, *args, **kwargs):
        raise NotImplementedError()


class AnonymousBaseHandler(BaseHandler):
    """
    Anonymous handler.
    """
    is_anonymous = True
    allowed_methods = ('GET',)
