import difflib

from django.db.models.aggregates import Count

from activity_logger.logger import Logger
from common.constants import STREAM_TYPE_TAG, ACTIVITY_DATA_TAG, ACTIVITY_TYPE_TAG_INTEREST_ADDED, \
    ACTIVITY_DATA_USERNAME, ACTIVITY_TYPE_TAG_INTEREST_REMOVED, EVENT_TYPE_FOLLOW_TAG
from shoutit.models import User, Tag, Stream
from shoutit.controllers import event_controller, user_controller


def get_tag(name):
    try:
        return Tag.objects.get(Name__iexact=name)
    except Tag.DoesNotExist:
        return None


def get_top_tags(limit=10, country=None, city=None):
    filters = {}
    if country:
        filters['Followers__Country'] = country

    if city:
        filters['Followers__City'] = city

    top_tags = Tag.objects.filter(**filters).values('pk').annotate(
        listeners_count=Count('Followers')
    ).filter(listeners_count__gte=1).values('Name', 'listeners_count', 'image').order_by('-listeners_count')[:limit]
    return list(top_tags)


def setTagParent(child_id, parent_name):
    tag = Tag.objects.get(pk=child_id)
    parent = get_tag(parent_name)
    if len(tag.ChildTags.all()):
        tag.Parent = None
    else:
        tag.Parent = parent
    tag.save()


def GetSynonymParent(name):
    parentsTag = Tag.objects.filter(Parent__isnull=True)
    max = 0
    max_index = 0
    ite = 0
    for tag in parentsTag:
        ratio = difflib.SequenceMatcher(None, name, tag.Name).ratio()
        if ratio > max:
            max = ratio
            max_index = ite
        ite += 1

    if len(parentsTag) != 0 and max > 0.4:
        return parentsTag[max_index]
    else:
        return None


def get_or_create_tag(name, creator, is_parent):
    tag, created = Tag.objects.get_or_create(Name=name)
    if created:
        stream = Stream(Type=STREAM_TYPE_TAG)
        stream.save()
        tag.Stream = stream
        tag.Creator = creator
        tag.save(update_fields=['Stream', 'Creator'])
    return tag


def get_or_create_tags(tags, creator):
    return [get_or_create_tag(tag, creator, False) for tag in tags]


# todo: remove
def AddToUserInterests(request, tag, user):
    if isinstance(user, User):
        user = user.profile
    if isinstance(tag, unicode):
        tag = Tag.objects.filter(Name__iexact=tag)
        if not tag:
            raise Tag.DoesNotExist()
        else:
            tag = tag[0]
    if tag not in user.Interests.all():
        user.Interests.add(tag)
        user_controller.FollowStream(request, user, tag.Stream)
        user.save()
        event_controller.register_event(user.user, EVENT_TYPE_FOLLOW_TAG, tag)
        Logger.log(request, type=ACTIVITY_TYPE_TAG_INTEREST_ADDED, data={ACTIVITY_DATA_TAG: tag.pk, ACTIVITY_DATA_USERNAME: user.username})


# todo: remove
def RemoveFromUserInterests(request, tag, user):
    if isinstance(user, User):
        user = user.profile
    if isinstance(tag, unicode):
        tag = Tag.objects.filter(Name__iexact=tag)[:]
        if not tag:
            raise Tag.DoesNotExist()
        else:
            tag = tag[0]
    if tag in user.Interests.all():
        user_controller.UnfollowStream(request, user, tag.Stream)
        user.Interests.remove(tag)
        user.save()

        Logger.log(request, type=ACTIVITY_TYPE_TAG_INTEREST_REMOVED,
                   data={ACTIVITY_DATA_TAG: tag.pk, ACTIVITY_DATA_USERNAME: user.username})


def search_tags(query='', limit=10):
    tags = Tag.objects.filter(Name__icontains=query).values('Name', 'image')[:limit]
    return list(tags)