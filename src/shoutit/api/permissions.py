# -*- coding: utf-8 -*-
"""

"""
from __future__ import unicode_literals

from django.conf import settings
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import (BasePermission)

SAFE_METHODS = ('GET', 'HEAD', 'OPTIONS')
MODIFY_METHODS = ['PUT', 'PATCH', 'DELETE']


class IsSecure(BasePermission):
    """
    Custom permission to only allow secure connections.
    """

    def has_permission(self, request, view):
        if settings.ENFORCE_SECURE and not request.is_secure():
            raise ValidationError({
                'error': 'invalid_request',
                'error_description': "A secure connection is required."})
        return True


class IsOwner(BasePermission):
    """
    Custom permission to only allow owners of an object to view or edit it.
    Model instances are expected to include an `owner` attribute.
    """

    def has_object_permission(self, request, view, obj):
        assert hasattr(obj, 'owner'), "obj must have an `owner` attribute"
        return obj.owner == request.user


class CanContribute(BasePermission):
    """
    Custom permission to check whether the logged in user can contribute to it or not.
    Model instances are expected to include an `can_contribute` method.
    """

    def has_object_permission(self, request, view, obj):
        assert hasattr(obj, 'can_contribute'), "obj must have a `can_contribute` attribute"
        return obj.can_contribute(request.user)


class IsAdminOrCanContribute(BasePermission):
    """
    Custom permission to only allow admins to edit and contributors of an object to view and participate.
    Model instances are expected to include `is_admin` and `can_contribute` methods that accept a user instance.
    """

    def has_object_permission(self, request, view, obj):
        assert hasattr(obj, 'can_contribute') and hasattr(obj, 'admins'), "obj must have `is_admin` and `can_contribute` attributes"
        if request.method == 'PATCH':
            return obj.is_admin(request.user)
        else:
            return obj.can_contribute(request.user)


class IsOwnerOrReadOnly(BasePermission):
    """
    Custom permission to only allow owners of an object to edit it. Others will be able to view it.
    Model instances are expected to include an `owner` attribute.
    """

    def has_object_permission(self, request, view, obj):
        assert hasattr(obj, 'owner'), "obj must have an `owner` attribute"
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in SAFE_METHODS:
            return True

        # Write permissions are only allowed to the owner of the object.
        return obj.owner == request.user


class IsOwnerOrContributorsReadOnly(BasePermission):
    """
    Custom permission to only allow owners of an object to edit it. Contributors will be able to view it.
    Model instances are expected to include `owner` and `contributors` attributes.
    """

    def has_object_permission(self, request, view, obj):
        assert hasattr(obj, 'owner'), "obj must have an `owner` attribute"
        assert hasattr(obj, 'contributors'), "obj must have a `contributors` attribute"

        # Read permissions are only allowed to Contributors,
        # so we'll allow GET, HEAD or OPTIONS requests to them.
        if request.method in SAFE_METHODS and request.user in obj.contributors:
            return True

        # Write permissions are only allowed to the owner of the object.
        return obj.owner == request.user


class IsOwnerModify(BasePermission):
    """
    Custom permission to only allow owner of an object to modify it.
    """

    def has_object_permission(self, request, view, obj):
        assert hasattr(obj, 'owner'), "obj must have an `owner` attribute"

        if request.method in MODIFY_METHODS:
            return obj.owner == request.user
        return True
