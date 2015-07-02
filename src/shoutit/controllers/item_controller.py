from __future__ import unicode_literals
from shoutit.models import Item, Video, Currency


def create_item(name, description, price, currency, images=None, videos=None):
    currency = currency
    item = Item.objects.create(name=name, description=description, price=price, currency=currency, images=images)

    if videos:
        for v in videos:
            # todo: better handling
            try:
                video = Video.objects.create(url=v['url'], thumbnail_url=v['thumbnail_url'], provider=v['provider'],
                                             id_on_provider=v['id_on_provider'], duration=v['duration'])
                item.videos.add(video)
            except:
                pass

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
    if images:
        item.images = images
    if videos:
        item.videos.all().delete()
        for v in videos:
            # todo: better handling
            try:
                video = Video.objects.create(url=v['url'], thumbnail_url=v['thumbnail_url'], provider=v['provider'],
                                             id_on_provider=v['id_on_provider'], duration=v['duration'])
                item.videos.add(video)
            except:
                pass
    item.save()
    return item
