from __future__ import unicode_literals
from django.contrib.contenttypes.models import ContentType

from common.constants import POST_TYPE_EVENT
from shoutit.models import Event


def register_event(user, event_type, attached_object=None):
    event = Event.objects.create(user=user, type=POST_TYPE_EVENT, event_type=event_type, attached_object=attached_object)
    user.profile.stream.add_post(event)


def delete_event_about_obj(attached_object):
    ct = ContentType.objects.get_for_model(attached_object)
    try:
        event = Event.objects.get(content_type=ct, object_id=attached_object.id)
        event.is_disabled = True
        event.save()
    except Event.DoesNotExist:
        pass
