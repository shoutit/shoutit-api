from django.core.exceptions import ObjectDoesNotExist
import ShoutWebsite
from ShoutWebsite.constants import *


def GetItemByID(item_id):
	return Item.objects.get(pk = item_id)

def CreateItem(name, price, images, currency, description = ''):
	currency = ShoutWebsite.controllers.shout_controller.GetCurrency(currency)
	item = Item(Name = name, Price = price, Currency = currency, Description = description)
	item.save()

	if images:
		images.sort()

	for image in images:
		stored_image = StoredImage()
		stored_image.Item = item
		stored_image.Image = image
		stored_image.save()

	if images:
		try:
			ShoutWebsite.controllers.shout_controller.MakeCloudThumbnailsForImage(images[0])
		except :
			pass
	return item


def EditItem(item,name = None, price = None, images = None, currency = None, description = None):
	if isinstance(item,int):
		item = GetItemByID(item)

	if name:
		item.Name = name
	if price:
		item.Price = price
	if currency:
		shout_currency = ShoutWebsite.controllers.shout_controller.GetCurrency(currency)
		item.Currency = shout_currency
	if description:
		item.Description = description

	if images:
		images.sort()
		old_images = item.GetImages()
		if len(old_images):
			for old_img in old_images:
				old_img.delete()


	for image in images:
		try:
			existed = StoredImage.objects.get(Image__exact = image)
		except ObjectDoesNotExist, e:
			stored_image = StoredImage()
			stored_image.Item = item
			stored_image.Image = image
			stored_image.save()
		except ShoutWebsite.controllers.shout_controller.MultipleObjectsReturned, e:
			pass

	if images:
		ShoutWebsite.controllers.shout_controller.MakeCloudThumbnailsForImage(images[0])

	item.save()
	return item


from ShoutWebsite import constants, utils
import ShoutWebsite.controllers.shout_controller
from ShoutWebsite.models import Item, Post, Trade, StoredImage