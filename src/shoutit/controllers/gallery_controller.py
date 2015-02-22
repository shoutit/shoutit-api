from common.constants import *
from shoutit.controllers.tag_controller import get_or_create_tags


def GetBusinessGalleryItems(business, start_index=None, end_index=None):
    gallery = GetBusinessGallery(business)
    if gallery:
        galleryItems = GalleryItem.objects.filter(Gallery=gallery, IsDisable=False, muted=False).select_related('item',
                                                                                                                  'item__Currency').order_by(
            '-DateCreated')[start_index:end_index]
        items_pk = [galleryItem.item.pk for galleryItem in galleryItems]
        stored_images = StoredImage.objects.filter(item__pk__in=items_pk).select_related('item')
        items = []
        for gallery_item in galleryItems:
            gallery_item.item.images = [stored_image.image for stored_image in stored_images if
                                        stored_image.item.pk == gallery_item.item.pk]
            items.append(gallery_item.item)
        return items
    else:
        return []


def GetBusinessGallery(business):
    gallery = business.Galleries.all()
    if gallery:
        return gallery[0]
    else:
        return None


def AddItemToGallery(user, gallery, name, price, images, currency, description):
    item = item_controller.create_item(name=name, price=price, currency=currency, images=images, description=description)
    galleryItem = GalleryItem(Gallery=gallery, item=item)
    if galleryItem:
        galleryItem.save()
        event_controller.register_event(user, EVENT_TYPE_GALLERY_ITEM, galleryItem)
    return item


def DeleteItemFromGallery(item_id):
    item = item_controller.get_item(item_id)
    gallery_item = GalleryItem.objects.filter(item=item)
    if gallery_item:
        gallery_item = gallery_item[0]
        gallery_item.IsDisable = True
        Post.objects.filter(pk__in=[trade.pk for trade in Trade.objects.filter(item=item)]).update(is_disabled=True)
        gallery_item.save()


# def HideItemFromGallery(item,gallery):
#	gallery_item = GalleryItem.objects.filter(item=item,Gallery=gallery)
#	if gallery_item:
#		gallery_item = gallery_item[0]
#		gallery_item.muted = True
#		gallery_item.save()

def ShoutItem(request, business, item, text, longitude, latitude, country, city, address, tags):
    stream = business.Business.Stream
    stream2 = business.Business.stream2
    trade = Trade(text=text, longitude=longitude, latitude=latitude, user=business,
                  type=POST_TYPE_OFFER, item=item, country=country, city=city, address=address)

    trade.save()

    stream.PublishShout(trade)
    stream2.add_post(trade)
    for tag in get_or_create_tags(tags, business):
        trade.tags.add(tag)
        tag.Stream.PublishShout(trade)
        tag.stream2.add_post(trade)

    if trade:
        trade.StreamsCode = str([f.pk for f in trade.Streams.all()])[1:-1]
        trade.save()

    save_relocated_shouts(trade, STREAM_TYPE_RECOMMENDED)
    save_relocated_shouts(trade, STREAM_TYPE_RELATED)

    event_controller.register_event(request.user, EVENT_TYPE_SHOUT_OFFER, trade)
    return trade


from shoutit.controllers import event_controller, item_controller
from shoutit.models import GalleryItem, Post, Trade, StoredImage
from shoutit.controllers.shout_controller import save_relocated_shouts
