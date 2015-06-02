from __future__ import unicode_literals
from common.constants import (DEFAULT_PAGE_SIZE,
                              POST_TYPE_REQUEST, POST_TYPE_OFFER, Stream_TYPE_PROFILE,
                              Stream_TYPE_TAG,
                              EVENT_TYPE_LISTEN_TO_USER, EVENT_TYPE_LISTEN_TO_TAG)
from common.utils import process_tags
from shoutit.controllers import notifications_controller, event_controller
from shoutit.models import Tag, Shout, Stream, Listen, Profile, User


post_types = {
    'all': [POST_TYPE_REQUEST, POST_TYPE_OFFER],
    None: [POST_TYPE_REQUEST, POST_TYPE_OFFER],

    'requests': [POST_TYPE_REQUEST],
    'request': [POST_TYPE_REQUEST],
    POST_TYPE_REQUEST: [POST_TYPE_REQUEST],

    'offers': [POST_TYPE_OFFER],
    'offer': [POST_TYPE_OFFER],
    POST_TYPE_OFFER: [POST_TYPE_OFFER],
}


def get_shouts_by_pks(pks):
    """
    Select shouts from database according to their IDs, including other objects related to every shout.
    pks: array of shout IDs
    return: array of shout objects
    """
    if not pks:
        return []
    # todo: optimize
    shout_qs = Shout.objects.get_valid_shouts().select_related(
        'item', 'item__currency', 'user', 'user__profile').filter(pk__in=pks)
    return shout_qs


# todo: use country, city, etc
def get_stream_shouts(stream, start_index=0, end_index=DEFAULT_PAGE_SIZE, show_expired=False,
                      country=None, city=None):
    """
    return the shouts (offers/requests) in a stream
    """
    shout_types = [POST_TYPE_REQUEST, POST_TYPE_OFFER]
    post_ids_qs = stream.posts.get_valid_posts(types=shout_types).order_by(
        '-date_published').values_list('id', flat=Shout)[start_index:end_index]
    shouts = list(Shout.objects.filter(id__in=list(post_ids_qs)).order_by('-date_published'))
    return shouts


def get_stream_shouts_qs(stream, shout_type=None):
    """
    return the Shouts Queryset (offers/requests) in a stream
    """
    types = post_types[shout_type]
    qs = Shout.objects.get_valid_shouts(types=types).filter(streams2=stream).order_by(
        '-date_published')
    return qs


def get_stream_shouts_count(stream):
    """
    return the total number of shouts (offers/requests) in a stream
    """
    return stream.posts.filter(type__in=[POST_TYPE_REQUEST, POST_TYPE_OFFER]).count()


def get_stream_listeners(stream, count_only=False):
    """
    return the users who are listening to this stream
    """
    if count_only:
        listeners = stream.listeners.count()
    else:
        listeners = stream.listeners.all()
    return listeners


def get_user_listening(user, listening_type=None, count_only=False):
    """
    return the objects (Profiles, tags, etc) that the users are listening to their streams
    """
    stream_types = {
        'users': Stream_TYPE_PROFILE,
        'profiles': Stream_TYPE_PROFILE,
        'tags': Stream_TYPE_TAG,
        Stream_TYPE_PROFILE: Stream_TYPE_PROFILE,
        Stream_TYPE_TAG: Stream_TYPE_TAG,
    }
    assert listening_type in stream_types.keys(), "invalid listening type {}".format(listening_type)
    stream_type = stream_types[listening_type]

    if stream_type:
        qs = Listen.objects.filter(listener=user, stream__type=stream_type)
    else:
        qs = Listen.objects.filter(listener=user)

    if count_only:
        return qs.count()
    else:
        listens = qs.all()
        stream_pks = [listen.stream_id for listen in listens]
        streams = Stream.objects.filter(pk__in=stream_pks)
        object_ids = [stream.object_id for stream in streams]

        if stream_type == Stream_TYPE_PROFILE:
            return list(Profile.objects.filter(pk__in=object_ids))
        elif stream_type == Stream_TYPE_TAG:
            return list(Tag.objects.filter(pk__in=object_ids))
        else:
            return listens


def get_user_listening_qs(user, listening_type):
    """
    return the queryset of Users or tags that the users are listening to
    normally the user listens to a profile stream, but for ease we return the User classes with Profile pre-fetched.
    """
    stream_types = {
        'users': Stream_TYPE_PROFILE,
        'tags': Stream_TYPE_TAG,
        Stream_TYPE_PROFILE: Stream_TYPE_PROFILE,
        Stream_TYPE_TAG: Stream_TYPE_TAG,
    }
    assert listening_type in stream_types.keys(), "invalid listening type {}".format(listening_type)
    stream_type = stream_types[listening_type]

    # todo: find way with only one query to get the listening
    object_ids = user.listening.filter(type=stream_type).values_list('object_id', flat=True)

    if stream_type == Stream_TYPE_PROFILE:
        return User.objects.filter(profile__id__in=object_ids).prefetch_related('profile')
    if stream_type == Stream_TYPE_TAG:
        return Tag.objects.filter(id__in=object_ids)


def listen_to_stream(listener, stream, request=None):
    """
    add a stream to user listening
    """
    try:
        Listen.objects.get(listener=listener, stream=stream)
    except Listen.DoesNotExist:
        listen = Listen(listener=listener, stream=stream)
        listen.save()
        if stream.type == Stream_TYPE_PROFILE:
            notifications_controller.notify_user_of_listen(stream.owner.user, listener, request)
            event_controller.register_event(listener, EVENT_TYPE_LISTEN_TO_USER, stream.owner)
        elif stream.type == Stream_TYPE_TAG:
            event_controller.register_event(listener, EVENT_TYPE_LISTEN_TO_TAG, stream.owner)


def remove_listener_from_stream(listener, stream):
    """
    remove a stream from user listening
    """
    Listen.objects.filter(listener=listener, stream=stream).delete()


def filter_posts_qs(qs, post_type=None):
    types = post_types[post_type]
    return qs.filter(type__in=types)


def filter_shouts_qs_by_tags(qs, tags=None):
    if not tags:
        return qs

    tags = process_tags(tags)
    for tag_name in tags:
        qs = qs.filter(tags=tag_name)
    return qs
