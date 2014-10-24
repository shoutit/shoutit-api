import difflib
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.db.models.aggregates import Count

def GetTag(name):
    tag = Tag.objects.filter(Name__iexact = name)
    if tag:
        return tag[0]
    else:
        return None

def GetTagTrades(tag):
    trades = Trade.objects.GetValidTrades().filter(Tags = tag).select_related('OwnerUser','OwnerUser__Profile','Item','Item__Currency')
    trades = shout_controller.get_trade_images(trades)
    return list(trades)


def GetTags(type):
    if type == "Parents":
        return Tag.objects.filter(Parent__isnull=True)
    elif type == "Childs":
        return Tag.objects.filter(Parent__isnull=False)
    elif type == "All":
        return Tag.objects.all().order_by("Name")


def GetTopTags(limit=10, country='', city=''):
    if not limit:
        limit = 10
    if not country:
        country = ''
    if not city:
        city = ''


    filters = {}
    if len(country.strip()):
        filters['Followers__Country'] = country

    if len(city.strip()):
        filters['Followers__City'] = city

    top_tags = Tag.objects.filter(**filters).values('id').annotate(listen_count=Count('Followers')).values('Name', 'listen_count').order_by('-listen_count')[:limit]
    return list(top_tags)


def setTagParent(child_id,parent_name):
    tag = Tag.objects.get(pk = child_id)
    parent = GetTag(parent_name)
    if len(tag.ChildTags.all()):
        tag.Parent = None
    else:
        tag.Parent = parent
    tag.save()



def GetSynonymParent(name):
    parentsTag = Tag.objects.filter(Parent__isnull = True)
    max = 0
    max_index = 0
    ite = 0
    for tag in parentsTag:
        ratio = difflib.SequenceMatcher(None, name, tag.Name).ratio()
        if ratio > max:
            max = ratio
            max_index = ite
        ite+=1

    if len(parentsTag) != 0 and max > 0.4:
        return parentsTag[max_index]
    else:
        return None


def GetOrCreateTag(request, name, creator, isParent):
    import re
    name = re.sub('[\s,/,&]', '-', name)
    name = re.sub('[-]+', '-', name)

    tag = Tag.objects.filter(Name__iexact = name)
    if tag:
        return tag[0]
    else:
        stream = Stream(Type = STREAM_TYPE_TAG)
        stream.save()
        tag = Tag.objects.create(Name = name, Creator = creator, Stream = stream, Parent = None)
        Logger.log(request, type=ACTIVITY_TYPE_TAG_CREATED, data={ACTIVITY_DATA_TAG : tag.id})
        return tag


def GetOrCreateTags(request, names, creator):
    result = []
    for name in names:
        if name and name.strip() != '':
            result.append(GetOrCreateTag(request, name.strip(), creator, False))
    return result


def AddToUserInterests(request, tag, user):
    if isinstance(user, User):
        user = user.Profile
    if isinstance(tag, unicode):
        tag = Tag.objects.filter(Name__iexact = tag)
        if not tag:
            raise ObjectDoesNotExist()
        else:
            tag = tag[0]
    if tag not in user.Interests.all():
        user.Interests.add(tag)
        apps.shoutit.controllers.user_controller.FollowStream(request, user,tag.Stream)
        user.save()
        event_controller.RegisterEvent(user.User, EVENT_TYPE_FOLLOW_TAG, tag)
        Logger.log(request, type=ACTIVITY_TYPE_TAG_INTEREST_ADDED, data={ACTIVITY_DATA_TAG : tag.id, ACTIVITY_DATA_USERNAME : user.username})


def RemoveFromUserInterests(request, tag, user):
    if isinstance(user, User):
        user = user.Profile
    if isinstance(tag, unicode):
        tag = Tag.objects.filter(Name__iexact = tag)[:]
        if not tag:
            raise ObjectDoesNotExist()
        else:
            tag = tag[0]
    if tag in user.Interests.all():
        apps.shoutit.controllers.user_controller.UnfollowStream(request, user, tag.Stream)
        user.Interests.remove(tag)
        user.save()

        Logger.log(request, type=ACTIVITY_TYPE_TAG_INTEREST_REMOVED, data={ACTIVITY_DATA_TAG : tag.id, ACTIVITY_DATA_USERNAME : user.username})


def SearchTags(keyword, limit):
    tags = Tag.objects.filter(Name__icontains = keyword).values_list('Name', flat=True)[:limit]
    return tags


def TagFollowers(tagName):
    tag = GetTag(tagName)
    followers = tag.Stream.userprofile_set.all()
    return followers

from apps.ActivityLogger.logger import Logger
from apps.shoutit.constants import STREAM_TYPE_TAG, ACTIVITY_TYPE_TAG_CREATED, ACTIVITY_DATA_TAG, ACTIVITY_TYPE_TAG_INTEREST_ADDED, ACTIVITY_DATA_USERNAME, ACTIVITY_TYPE_TAG_INTEREST_REMOVED, EVENT_TYPE_FOLLOW_TAG, POST_TYPE_SELL, POST_TYPE_BUY
import apps.shoutit.controllers.user_controller,event_controller,shout_controller
from apps.shoutit.models import Tag, Stream, Trade, StoredImage