# -*- coding: utf-8 -*-
"""

"""
from __future__ import unicode_literals

from rest_framework import permissions


class IsOwner(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to view or edit it.
    Model instances are expected to include an `owner` attribute.
    """

    def has_object_permission(self, request, view, obj):
        assert hasattr(obj, 'owner'), "obj must have an `owner` attribute"
        return obj.owner == request.user


class IsContributor(permissions.BasePermission):
    """
    Custom permission to only allow contributors of an object to view or edit it.
    Model instances are expected to include an `owner` attribute.
    """

    def has_object_permission(self, request, view, obj):
        assert hasattr(obj, 'contributors'), "obj must have a `contributors` attribute"
        return request.user in obj.contributors


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to edit it. Others will be able to view it.
    Model instances are expected to include an `owner` attribute.
    """

    def has_object_permission(self, request, view, obj):
        assert hasattr(obj, 'owner'), "obj must have an `owner` attribute"
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions are only allowed to the owner of the object.
        return obj.owner == request.user


class IsOwnerOrContributorsReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to edit it. Contributors will be able to view it.
    Model instances are expected to include `owner` and `contributors` attributes.
    """

    def has_object_permission(self, request, view, obj):
        assert hasattr(obj, 'owner'), "obj must have an `owner` attribute"
        assert hasattr(obj, 'contributors'), "obj must have a `contributors` attribute"

        # Read permissions are only allowed to Contributors,
        # so we'll allow GET, HEAD or OPTIONS requests to them.
        if request.method in permissions.SAFE_METHODS and request.user in obj.contributors:
            return True

        # Write permissions are only allowed to the owner of the object.
        return obj.owner == request.user

