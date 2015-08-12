from __future__ import unicode_literals
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from shoutit.models import Item, Video
from shoutit.utils import error_logger


def create_item(name, description, price, currency, images=None, videos=None):
    # currency = currency  # todo: check!
    images = images or []
    item = Item.create(name=name, description=description, price=price, currency=currency, images=images)
    add_videos_to_item(item, videos)
    return item


def edit_item(item, name=None, description=None, price=None, currency=None, images=None, videos=None):
    if name:
        item.name = name
    if description:
        item.description = description
    if price:
        item.price = price
    if currency:
        item.currency = currency
    if images is not None:
        item.images = images
    item.save()
    add_videos_to_item(item, videos, remove_existing=True)
    return item


def add_videos_to_item(item, videos=None, remove_existing=False):
    if videos is not None:
        if remove_existing:
            item.videos.all().delete()
        for v in videos:
            # todo: better handling
            try:
                video = Video.create(url=v['url'], thumbnail_url=v['thumbnail_url'], provider=v['provider'],
                                     id_on_provider=v['id_on_provider'], duration=v['duration'])
                item.videos.add(video)
            except (KeyError, ValidationError, IntegrityError) as e:
                error_logger.warn(str(e))
