# -*- coding: utf-8 -*-
"""

"""
from __future__ import unicode_literals
from rest_framework import viewsets, mixins


class NoUpdateModelViewSet(mixins.ListModelMixin,
                           mixins.RetrieveModelMixin,
                           mixins.CreateModelMixin,
                           mixins.DestroyModelMixin,
                           viewsets.GenericViewSet):
    """
    A viewset that provides default `list()`, `retrieve()`, `create()` and `destroy()`  actions.
    """
    pass