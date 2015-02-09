from django.http import HttpResponseNotAllowed
from piston3.handler import BaseHandler


class TieredHandler(BaseHandler):
    allowed_methods = ('POST', 'DELETE', 'PUT', 'GET')

    def __init__(self, methods_map=None):
        BaseHandler.__init__(self)
        self.methods_map = methods_map

    def read(self, request, *args, **kwargs):
        if 'GET' in self.methods_map:
            return self.methods_map['GET'](request, *args, **kwargs)
        else:
            return HttpResponseNotAllowed(self.methods_map.keys())

    def create(self, request, *args, **kwargs):
        if 'POST' in self.methods_map:
            return self.methods_map['POST'](request, *args, **kwargs)
        else:
            return HttpResponseNotAllowed(self.methods_map.keys())

    def update(self, request, *args, **kwargs):
        if 'PUT' in self.methods_map:
            return self.methods_map['PUT'](request, *args, **kwargs)
        else:
            return HttpResponseNotAllowed(self.methods_map.keys())

    def delete(self, request, *args, **kwargs):
        if 'DELETE' in self.methods_map:
            return self.methods_map['DELETE'](request, *args, **kwargs)
        else:
            return HttpResponseNotAllowed(self.methods_map.keys())