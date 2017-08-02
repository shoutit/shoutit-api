from django.core.exceptions import ValidationError
from django.db import IntegrityError

from common.constants import (LISTEN_TYPE_PAGE, LISTEN_TYPE_PROFILE)
from shoutit.controllers import notifications_controller
from shoutit.models import Listen2, User


def get_object_listeners(obj, count_only=False):
    """
    Return the users who are listening to this object
    """
    listen_type, target = Listen2.listen_type_and_target_from_object(obj)
    listeners_ids = Listen2.objects.filter(type=listen_type, target=target).values_list('user', flat=True)
    if count_only:
        return listeners_ids.count()
    else:
        return User.objects.filter(id__in=listeners_ids)


def listen_to_object(user, obj, api_client=None, api_version=None):
    """
    """
    listen_type, target = Listen2.listen_type_and_target_from_object(obj)

    listen = Listen2(user=user, type=listen_type, target=target)
    listen.api_client, listen.api_version = api_client, api_version
    try:
        listen.save()
        if listen_type in [LISTEN_TYPE_PROFILE, LISTEN_TYPE_PAGE]:
            notifications_controller.notify_user_of_listen(obj.user, user)
    except (ValidationError, IntegrityError):
        pass


def listen_to_objects(user, objects, api_client=None, api_version=None):
    """
    """
    # Todo: optimize!
    for obj in objects:
        listen_to_object(user, obj, api_client=api_client, api_version=api_version)


def stop_listening_to_object(user, obj):
    """
    """
    listen_type, target = Listen2.listen_type_and_target_from_object(obj)
    Listen2.objects.filter(user=user, type=listen_type, target=target).delete()


def stop_listening_to_objects(user, objects):
    """
    """
    # Todo: optimize!
    for obj in objects:
        stop_listening_to_object(user, obj)
