"""

"""
from __future__ import unicode_literals

import uuid
from importlib import import_module

from django.contrib.auth.models import AnonymousUser
from rest_framework import serializers as rest_serializers

from shoutit.api.v3.exceptions import ERROR_REASON
from shoutit.utils import create_fake_request


def serialize_attached_object(attached_object, version, user=None):
    from ..models import Conversation, Message, User, Notification
    shoutit_serializers = import_module('shoutit.api.%s.serializers' % version)

    # Create fake Request and set request.user to the notified user as if he was requesting it.
    request = create_fake_request(version)
    request.user = user or AnonymousUser()

    if isinstance(attached_object, (dict, list)):
        return attached_object
    if isinstance(attached_object, User):
        # Use ProfileDetailSerializer if the user is the one getting his own profile
        if user and user.id == request.user.id:
            serializer = shoutit_serializers.ProfileDetailSerializer
        else:
            serializer = shoutit_serializers.ProfileSerializer
    elif isinstance(attached_object, Message):
        serializer = shoutit_serializers.MessageSerializer
    elif isinstance(attached_object, Conversation):
        if getattr(attached_object, 'detailed', True):
            serializer = shoutit_serializers.ConversationDetailSerializer
        else:
            serializer = shoutit_serializers.ConversationSerializer
    elif isinstance(attached_object, Notification):
        serializer = shoutit_serializers.NotificationSerializer
    elif hasattr(attached_object, 'serializer') and callable(attached_object.serializer):
        serializer = attached_object.serializer(version)
    else:
        serializer = None

    if serializer:
        attached_object_dict = serializer(attached_object, context={'request': request}).data
    else:
        attached_object_dict = {}

    return attached_object_dict


class HasAttachedUUIDObjects(object):
    pass


class AttachedUUIDObjectMixin(object):
    """
    For UUID validation to work correctly, Subclasses must
    - inherit `AttachedUUIDObjectMixin` as their first super class.
    - be included as properties of a serializer that inherits `HasAttachedUUIDObjects` as its first super class
    """
    def to_internal_attached_value(self, data):
        model = self.Meta.model
        # Make sure no empty JSON body was posted
        if not data:
            data = {}
        # Validate the id only
        if isinstance(self.parent, HasAttachedUUIDObjects):
            if not isinstance(data, dict):
                raise rest_serializers.ValidationError(
                    'Invalid data. Expected a dictionary, but got %s' % type(data).__name__)
            object_id = data.get('id')
            if object_id == '':
                raise rest_serializers.ValidationError({'id': 'This field can not be empty'})
            if object_id:
                try:
                    uuid.UUID(object_id)
                    instance = model.objects.filter(id=object_id).first()
                except (ValueError, TypeError, AttributeError):
                    raise rest_serializers.ValidationError({'id': "'%s' is not a valid id" % object_id})
                else:
                    if not instance:
                        raise rest_serializers.ValidationError(
                            {'id': "%s with id '%s' does not exist" % (model.__name__, object_id)})
                    # Todo: utilize the fetched instance
                    self.instance = instance
                    return {'id': object_id}
            else:
                raise rest_serializers.ValidationError({'id': ("This field is required", ERROR_REASON.REQUIRED)})

    def to_internal_value(self, data):
        ret = self.to_internal_attached_value(data)
        if ret:
            return ret
        validated_data = super(AttachedUUIDObjectMixin, self).to_internal_value(data)
        return validated_data
