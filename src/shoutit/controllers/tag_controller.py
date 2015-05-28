from __future__ import unicode_literals
from common.utils import process_tag
from shoutit.models import Tag


def get_or_create_tag(name, creator=None):
    name = process_tag(name)
    if not name or not isinstance(name, basestring):
        return None
    tag, created = Tag.objects.get_or_create(name=name)
    if created:
        tag.creator = creator
        tag.save()
    return tag


def get_or_create_tags(names, creator=None):
    tags = []
    for name in names:
        tag = get_or_create_tag(name, creator)
        if tag:
            tags.append(tag)
    return tags
