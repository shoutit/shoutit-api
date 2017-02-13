# -*- coding: utf-8 -*-
"""

"""
from django.utils.translation import ugettext_lazy as _
from rest_framework import exceptions
from rest_framework.versioning import NamespaceVersioning


class ShoutitNamespaceVersioning(NamespaceVersioning):
    invalid_version_message = _('Invalid version in URL path. Please use version: %(version)s')

    def determine_version(self, request, *args, **kwargs):
        resolver_match = getattr(request, 'resolver_match', None)
        if resolver_match is None or not resolver_match.namespace:
            return self.default_version
        version = resolver_match.namespace
        if not self.is_allowed_version(version):
            raise exceptions.NotFound(self.invalid_version_message % {'version': self.default_version})
        return version

    def reverse(self, viewname, args=None, kwargs=None, request=None, format=None, **extra):
        if request.version is not None:
            if viewname.startswith(request.version + ':'):
                viewname = viewname[len(request.version) + 1:]
            viewname = self.get_versioned_viewname(viewname, request)
        return super(NamespaceVersioning, self).reverse(viewname, args, kwargs, request, format, **extra)
