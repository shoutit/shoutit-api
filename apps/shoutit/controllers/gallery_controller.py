from common.constants import *
from apps.shoutit.controllers.tag_controller import GetOrCreateTags


def GetBusinessGalleryItems(business, start_index=None, end_index=None):
    gallery = GetBusinessGallery(business)
    if gallery:
        galleryItems = GalleryItem.objects.filter(Gallery=gallery, IsDisable=False, IsMuted=False).select_related('Item',
                                                                                                                  'Item__Currency').order_by(
            '-DateCreated')[start_index:end_index]
        items_pk = [galleryItem.Item.pk for galleryItem in galleryItems]
        stored_images = StoredImage.objects.filter(Item__pk__in=items_pk).select_related('Item')
        items = []
        for gallery_item in galleryItems:
            gallery_item.Item.images = [stored_image.image for stored_image in stored_images if
                                        stored_image.Item.pk == gallery_item.Item.pk]
            items.append(gallery_item.Item)
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
    galleryItem = GalleryItem(Gallery=gallery, Item=item)
    if galleryItem:
        galleryItem.save()
        event_controller.RegisterEvent(user, EVENT_TYPE_GALLERY_ITEM, galleryItem)
    return item


def DeleteItemFromGallery(item_id):
    item = item_controller.get_item(item_id)
    gallery_item = GalleryItem.objects.filter(Item=item)
    if gallery_item:
        gallery_item = gallery_item[0]
        gallery_item.IsDisable = True
        Post.objects.filter(pk__in=[trade.pk for trade in Trade.objects.filter(Item=item)]).update(IsDisabled=True)
        gallery_item.save()


# def HideItemFromGallery(item,gallery):
#	gallery_item = GalleryItem.objects.filter(Item=item,Gallery=gallery)
#	if gallery_item:
#		gallery_item = gallery_item[0]
#		gallery_item.IsMuted = True
#		gallery_item.save()

def ShoutItem(request, business, item, text, longitude, latitude, country, city, address, tags):
    stream = business.Business.Stream
    stream2 = business.Business.stream2
    trade = Trade(Text=text, Longitude=longitude, Latitude=latitude, OwnerUser=business,
                  Type=POST_TYPE_OFFER, Item=item, CountryCode=country, ProvinceCode=city, Address=address)

    trade.save()

    stream.PublishShout(trade)
    stream2.add_post(trade)
    for tag in GetOrCreateTags(request, tags, business):
        trade.Tags.add(tag)
        tag.Stream.PublishShout(trade)
        tag.stream2.add_post(trade)

    if trade:
        trade.StreamsCode = str([f.pk for f in trade.Streams.all()])[1:-1]
        trade.save()

    save_relocated_shouts(trade, STREAM_TYPE_RECOMMENDED)
    save_relocated_shouts(trade, STREAM_TYPE_RELATED)

    event_controller.RegisterEvent(request.user, EVENT_TYPE_SHOUT_OFFER, trade)
    return trade


from apps.shoutit.controllers import event_controller, item_controller
from apps.shoutit.models import GalleryItem, Post, Trade, StoredImage
from apps.shoutit.controllers.shout_controller import save_relocated_shouts
