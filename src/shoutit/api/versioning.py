# -*- coding: utf-8 -*-
"""

"""
from __future__ import unicode_literals
from rest_framework.versioning import NamespaceVersioning


class ShoutitNamespaceVersioning(NamespaceVersioning):

    def reverse(self, viewname, args=None, kwargs=None, request=None, format=None, **extra):
        if request.version is not None:
            if viewname.startswith(request.version + ':'):
                viewname = viewname[len(request.version) + 1:]
            viewname = self.get_versioned_viewname(viewname, request)
        return super(NamespaceVersioning, self).reverse(viewname, args, kwargs, request, format, **extra)
