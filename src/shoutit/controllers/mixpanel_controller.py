"""

"""
from __future__ import unicode_literals

from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from django_rq import job
from mixpanel import Mixpanel, BufferedConsumer

from shoutit.models.auth import AbstractProfile
from shoutit.monkey_patches import ShoutitJSONEncoder
from ..models import User
from ..utils import debug_logger

# Shoutit mixpanel
MAX_MP_BUFFER_SIZE = 50
buffered_consumer = BufferedConsumer(max_size=MAX_MP_BUFFER_SIZE)
shoutit_mp = Mixpanel(settings.MIXPANEL_TOKEN, consumer=buffered_consumer, serializer=ShoutitJSONEncoder)


def alias(alias_id, original):
    if not settings.USE_MIXPANEL:
        return
    return _alias.delay(alias_id, original)


@job(settings.RQ_QUEUE)
def _alias(alias_id, original):
    shoutit_mp.alias(alias_id, original)
    debug_logger.debug("MP aliased, alias_id: %s original: %s" % (alias_id, original))


def track_new_message(message):
    _track_new_message.delay(message)


@job(settings.RQ_QUEUE)
def _track_new_message(message):
    distinct_id = message.user.pk if message.user else 'system'
    track(distinct_id, 'new_message', message.track_properties, delay=False)


def track(distinct_id, event_name, properties=None, delay=True):
    # Todo: properties could be a callable that gets called when the tracking happens
    if not settings.USE_MIXPANEL:
        return
    if delay:
        return _track.delay(distinct_id, event_name, properties)
    else:
        return _track(distinct_id, event_name, properties)


@job(settings.RQ_QUEUE)
def _track(distinct_id, event_name, properties=None):
    properties = properties or {}
    shoutit_mp.track(distinct_id, event_name, properties)
    debug_logger.debug("Tracked %s for %s" % (event_name, distinct_id))


def add_to_mp_people(user_ids=None, flush=False):
    return _add_to_mp_people.delay(user_ids=user_ids, flush=flush)


# Todo (mo): handle Pages properties
@job(settings.RQ_QUEUE)
def _add_to_mp_people(user_ids=None, flush=False):
    users = User.objects.filter(id__in=user_ids).select_related('profile', 'page')

    for user in users:
        ap = user.ap
        properties = {
            '$first_name': user.first_name,
            '$last_name': user.last_name,

            'is_active': user.is_active,
            'is_activated': user.is_activated,
            'is_guest': user.is_guest,
            'type': user.v3_type_name,
            'username': user.username,

            '$created': user.date_joined,
            'last_login': user.last_login,

            '$country_code': ap.country,
            '$region': ap.state,
            '$city': ap.city,

            '$email': user.email,
            'platforms': map(lambda c: str(c.replace('shoutit-', '')), user.api_client_names),
            'api_versions': user.devices.values_list('api_version', flat=True).distinct(),
            '$phone': getattr(ap, 'mobile', None),
        }
        if user.apns_device:
            properties['$ios_devices'] = [user.apns_device.registration_id]
        if user.gcm_device:
            properties['$android_devices'] = [user.gcm_device.registration_id]

        attributes = ['image', 'gender', 'birthday']
        for attr in attributes:
            value = getattr(ap, attr, None)
            if value not in (None, ''):
                properties[attr] = value

        meta = {
            '$ignore_time': True  # Don't count this update as a user activity. 'Last Seen' will not be updated
        }
        shoutit_mp.people_set(user.pk, properties, meta)

    if flush:
        shoutit_mp._consumer.flush()

    users.update(on_mp_people=True)
    debug_logger.debug("Added / Updated %s MixPanel People record(s)" % len(user_ids))


@receiver(post_save)
def post_save_profile(sender, instance=None, created=False, **kwargs):
    if isinstance(instance, User):
        add_to_mp_people(user_ids=[instance.id], flush=settings.DEBUG)
    elif isinstance(instance, AbstractProfile):
        add_to_mp_people(user_ids=[instance.user_id], flush=settings.DEBUG)
    else:
        pass


def remove_from_mp_people(user_ids=None, flush=False):
    return _remove_from_mp_people.delay(user_ids=user_ids, flush=flush)


@job(settings.RQ_QUEUE)
def _remove_from_mp_people(user_ids=None, flush=False):
    for user_id in user_ids:
        shoutit_mp.people_delete(user_id)

    if flush:
        shoutit_mp._consumer.flush()

    User.objects.filter(id__in=user_ids).update(on_mp_people=False)
    debug_logger.debug("Removed %s MixPanel People record(s)" % len(user_ids))
