from shoutit.models import Item, Video, Currency


def create_item(name, price, currency, description, images=None, videos=None):
    currency = get_currency(currency)
    item = Item(name=name, price=price, currency=currency, description=description, images=images)
    item.save()

    if videos:
        for v in videos:
            # todo: better handling
            try:
                video = Video(item=item, url=v['url'], thumbnail_url=v['thumbnail_url'], provider=v['provider'],
                              id_on_provider=v['id_on_provider'], duration=v['duration'])
                video.save()
            except:
                pass

    return item


def edit_item(item, name=None, price=None, images=None, currency=None, description=None):

    if name:
        item.name = name
    if price:
        item.price = price
    if currency:
        item.currency = get_currency(currency)
    if description:
        item.description = description
    if images:
        item.images = images

    item.save()
    return item


def get_currency(currency_code):
    return Currency.objects.get(code__iexact=currency_code)
