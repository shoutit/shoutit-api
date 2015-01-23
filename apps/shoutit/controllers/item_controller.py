from apps.shoutit.models import Item, StoredImage, Video, Currency
from apps.shoutit.utils import make_cloud_thumbnails_for_image


def get_item(item_id):
    return Item.objects.get(pk=item_id)


def create_item(name, price, currency, images=None, videos=None, description=''):
    currency = get_currency(currency)
    item = Item(Name=name, Price=price, Currency=currency, Description=description)
    item.save()

    if images:
        images.sort()

        for image in images:
            stored_image = StoredImage()
            stored_image.Item = item
            stored_image.image = image
            stored_image.save()

        try:
            make_cloud_thumbnails_for_image(images[0])
        except BaseException, e:
            print e

    if videos:
        for v in videos:
            video = Video(item=item, url=v['url'], thumbnail_url=v['thumbnail_url'], provider=v['provider'],
                          id_on_provider=v['id_on_provider'], duration=v['duration'])
            video.save()

    return item


def edit_item(item, name=None, price=None, images=None, currency=None, description=None):
    if isinstance(item, int):
        item = get_item(item)

    if name:
        item.Name = name
    if price:
        item.Price = price
    if currency:
        shout_currency = get_currency(currency)
        item.Currency = shout_currency
    if description:
        item.Description = description

    if images:
        images.sort()
        old_images = item.get_images()
        if len(old_images):
            for old_img in old_images:
                old_img.delete()

    for image in images:
        try:
            existed = StoredImage.objects.get(Image__exact=image)
        except StoredImage.DoesNotExist:
            stored_image = StoredImage()
            stored_image.Item = item
            stored_image.image = image
            stored_image.save()
        except StoredImage.MultipleObjectsReturned, e:
            print e

    if images:
        make_cloud_thumbnails_for_image(images[0])

    item.save()
    return item


def get_currency(currency_code):
    return Currency.objects.get(Code__iexact=currency_code)
