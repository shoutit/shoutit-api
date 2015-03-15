# -*- coding: utf-8 -*-
"""

"""
from __future__ import unicode_literals
import uuid
from rest_framework import viewsets, mixins
from rest_framework.exceptions import ValidationError


class NoUpdateModelViewSet(mixins.ListModelMixin,
                           mixins.RetrieveModelMixin,
                           mixins.CreateModelMixin,
                           mixins.DestroyModelMixin,
                           viewsets.GenericViewSet):
    """
    A viewset that provides default `list()`, `retrieve()`, `create()` and `destroy()`  actions.
    """
    pass


class UUIDViewSetMixin(object):

    lookup_field = 'id'

    def get_object(self):
        value = self.kwargs.get(self.lookup_field)
        try:
            uuid.UUID(value)
        except:
            raise ValidationError({'detail': "'%s' is not a valid id." % value})

        return super(UUIDViewSetMixin, self).get_object()