from __future__ import unicode_literals

from django.conf import settings
from django.db import IntegrityError

from shoutit.models import Item, Video
from shoutit.utils import error_logger


def create_item(name, description, price, currency, images=None, videos=None, available_count=None, is_sold=None):
    images = images or []
    item = Item.create(save=False, name=name, description=description, price=price, currency=currency,
                       images=images[:settings.MAX_IMAGES_PER_ITEM])
    if available_count is not None:
        item.available_count = available_count
    if is_sold is not None:
        item.is_sold = is_sold
    item.save()
    add_videos_to_item(item, videos)
    return item


def edit_item(item, name=None, description=None, price=None, currency=None, images=None, videos=None,
              available_count=None, is_sold=None):
    # Can be unset
    item.name = name
    item.description = description
    item.price = price
    item.currency = currency

    # Can't be unset
    if images is not None:
        item.images = images
    if available_count is not None:
        item.available_count = available_count
    if is_sold is not None:
        item.is_sold = is_sold

    item.save()
    add_videos_to_item(item, videos, remove_existing=True)
    return item


def add_videos_to_item(item, videos=None, remove_existing=False):
    if videos is not None:
        if remove_existing:
            item.videos.all().delete()
        for v in videos[:settings.MAX_VIDEOS_PER_ITEM]:
            # todo: better handling
            try:
                video = Video.objects.create(url=v['url'], thumbnail_url=v['thumbnail_url'], provider=v['provider'],
                                             id_on_provider=v['id_on_provider'], duration=v['duration'])
                item.videos.add(video)
            except (KeyError, IntegrityError) as e:
                error_logger.warn(str(e), exc_info=True)
