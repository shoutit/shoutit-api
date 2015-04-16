import difflib

from django.db.models.aggregates import Count

from common.utils import process_tag_name
from shoutit.models import Tag


def get_tag(name):
    try:
        return Tag.objects.get(name__iexact=name)
    except Tag.DoesNotExist:
        return None


def get_top_tags(limit=10, country=None, city=None):
    filters = {}
    if country:
        filters['Followers__country'] = country

    if city:
        filters['Followers__city'] = city

    top_tags = Tag.objects.filter(**filters).values('pk').annotate(
        listeners_count=Count('Followers')
    ).filter(listeners_count__gte=1).values('name', 'listeners_count', 'image').order_by('-listeners_count')[:limit]
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
        ratio = difflib.SequenceMatcher(None, name, tag.name).ratio()
        if ratio > max:
            max = ratio
            max_index = ite
        ite += 1

    if len(parentsTag) != 0 and max > 0.4:
        return parentsTag[max_index]
    else:
        return None


def get_or_create_tag(name, creator=None):
    name = process_tag_name(name)
    if not name or not isinstance(name, basestring):
        return None
    tag, created = Tag.objects.get_or_create(name=name, Creator=creator)
    return tag


def get_or_create_tags(names, creator=None):
    tags = []
    for name in names:
        tag = get_or_create_tag(name, creator)
        if tag:
            tags.append(tag)
    return tags


def search_tags(query='', limit=10):
    tags = Tag.objects.filter(name__icontains=query).values('name', 'image')[:limit]
    return list(tags)
