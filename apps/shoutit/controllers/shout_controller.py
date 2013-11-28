import StringIO
from datetime import datetime, timedelta
import os
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned, PermissionDenied
from django.core.files.base import ContentFile
from django.db.models.expressions import F
from django.db.models.query_utils import Q
from ActivityLogger.logger import Logger
from ShoutWebsite.constants import *
from ShoutWebsite.utils import asynchronous_task, ToSeoFriendly
import settings


def GetPost(post_id, find_muted=False, find_expired=False):
	post = Post.objects.filter(pk__exact = post_id,IsDisabled = False).select_related('OwnerUser','OwnerUser__Business','OwnerBusiness__Profile')
	if not find_muted:
		post = post.filter(IsMuted = False)

	if not find_expired:
		today = datetime.today()
		days = timedelta(days = int(settings.MAX_EXPIRY_DAYS))
		begin = today - days
		post = post.filter(
			(~Q(Type = POST_TYPE_BUY) & ~Q(Type = POST_TYPE_SELL))
			|
			((Q(shout__ExpiryDate__isnull = True, DatePublished__range = (begin, today))

			| Q(shout__ExpiryDate__isnull = False, DatePublished__lte = F('shout__ExpiryDate'))
			)
			& (Q(Type = POST_TYPE_BUY) | Q(Type = POST_TYPE_SELL)))
		).select_related(depth=2)
	if post:
		post = post[0]
		if post.Type == POST_TYPE_SELL or post.Type == POST_TYPE_BUY:
			return post.shout.trade
		elif post.Type == POST_TYPE_EXPERIENCE:
			return post.experience
	else:
		return None

def DeletePost(post_id):
	post = Post.objects.get(pk = post_id)
	if not post:
		raise ObjectDoesNotExist()
	else:
		post.IsDisabled = True
		post.save()
		try:
			if post.Type == POST_TYPE_BUY or post.Type == POST_TYPE_SELL:
				event_controller.DeleteEventAboutObj(post.shout.trade)
			elif post.Type == POST_TYPE_DEAL:
				event_controller.DeleteEventAboutObj(post.shout.deal)
			elif post.Type == POST_TYPE_EXPERIENCE:
				event_controller.DeleteEventAboutObj(post.experience)
		except :
			pass


	
def RenewShout(request, shout_id, days = int(settings.MAX_EXPIRY_DAYS)):
	shout = Shout.objects.get(pk = shout_id)
	if not shout:
		raise ObjectDoesNotExist()
	else:
		now = datetime.now()
		shout.DatePublished = now
		shout.ExpiryDate = now + timedelta(days = days)
		shout.RenewalCount += 1
		shout.ExpiryNotified = False
		shout.save()

def NotifyPreExpiry():
	shouts = Shout.objects.all()
	for shout in shouts:
		if not shout.ExpiryNotified:
			expiry_date = shout.ExpiryDate
			if not expiry_date:
				expiry_date = shout.DatePublished + timedelta(days = settings.MAX_EXPIRY_DAYS)
			if (expiry_date - datetime.now()).days < settings.SHOUT_EXPIRY_NOTIFY:
				if shout.OwnerUser.email:
					ShoutWebsite.controllers.email_controller.SendExpiryNotificationEmail(shout.OwnerUser, shout)
					shout.ExpiryNotified = True
					shout.save()


def EditShout(request, shout_id, name = None, text = None, price = None, longitude = None, latitude = None, tags = [], shouter = None, country_code = None, province_code = None, address = None, currency = None, images = [], date_published = None, stream = None):
	shout = Shout.objects.get(pk = shout_id)

	if not shout:
		raise ObjectDoesNotExist()
	else:
		if shout.Type == constants.POST_TYPE_BUY or shout.Type == constants.POST_TYPE_SELL:

			if text:
				shout.Text = text
			if longitude:
				shout.Longitude = longitude
			if latitude:
				shout.Latitude = latitude
			if shouter:
				shout.shouter = shouter
			if province_code:
				shout.ProvinceCode = province_code
			if country_code:
				shout.CountryCode = country_code
			if address:
				shout.Address = address
			if date_published:
				shout.DatePublished  = date_published

			item_controller.EditItem(shout.trade.Item,name,price,images,currency)

			if stream and shout.Stream != stream:
				shout.Stream.UnPublishShout(shout)
				shout.Stream = stream
				stream.PublishShout(shout)

			if len(tags) and shouter:
				shout.OwnerUser = shouter
				shout.Tags.clear()
				for tag in ShoutWebsite.controllers.tag_controller.GetOrCreateTags(request, tags, shouter):
					shout.Tags.add(tag)
					tag.Stream.PublishShout(shout)
			shout.StreamsCode = str([f.id for f in shout.Streams.all()])[1:-1]

			shout.trade.save()
			shout.save()
			
			SaveRecolatedShouts(shout.trade, STREAM_TYPE_RELATED)
			return shout
	return None






def GetLandingShouts(DownLeftLat , DownLeftLng , UpRightLat , UpRightLng):
	filters = {
			'Latitude__gte' : DownLeftLat,
			'Latitude__lte' : UpRightLat,
			'Longitude__gte' : DownLeftLng,
			'Longitude__lte' : UpRightLng,
		}
	shouts = Trade.objects.GetValidTrades().filter(**filters).values('id', 'Type','Longitude','Latitude')[:10000]
	return shouts


def MakeCloudThumbnailsForImage(image_url):
	utils.make_image_thumbnail(image_url, 145, 'shout_images')
	utils.make_image_thumbnail(image_url, 85, 'shout_images')

def GetStreamAffectedByShout(shout):
	if isinstance(shout, int):
		shout = Shout.objects.get(pk = shout)
	if shout:
		return shout.Streams.all()
	return []


def TagsAffinity(user_interests, shout, tags):
	shout_tags = [tag for tag in tags if tag in shout.GetTags()]
	if shout_tags:
		return float(len(set(user_interests) & set(shout_tags))) / float(len(shout.GetTags()))
	else:
		return 0

@asynchronous_task()
def SaveRecolatedShouts(trade, stream_type):
	type = POST_TYPE_BUY
	if stream_type == STREAM_TYPE_RECOMMENDED:
		if trade.Type == POST_TYPE_BUY:
			type = POST_TYPE_SELL
		elif trade.Type == POST_TYPE_SELL:
			type = POST_TYPE_BUY
	elif stream_type == STREAM_TYPE_RELATED:
		if trade.Type == POST_TYPE_BUY:
			type = POST_TYPE_BUY
		if trade.Type == POST_TYPE_SELL:
			type = POST_TYPE_SELL

	shouts = ShoutWebsite.controllers.stream_controller.GetShoutRecommendedShoutStream(trade, type, 0, 10, stream_type == STREAM_TYPE_RECOMMENDED)
	stream = Stream(Type= stream_type)
	stream.save()
	if stream_type == STREAM_TYPE_RECOMMENDED:
		old_recommended = trade.RecommendedStream
		trade.RecommendedStream = stream
		trade.save()
		if old_recommended:
			old_recommended.delete()
	elif stream_type == STREAM_TYPE_RELATED:
		old_related = trade.RelatedStream
		trade.RelatedStream = stream
		trade.save()
		if old_related:
			old_related.delete()
	for shout in shouts:
		shout_wrap = ShoutWrap(Shout = shout, Stream = stream, Rank = shout.rank)
		shout_wrap.save()
		ShoutWebsite.controllers.stream_controller.PublishShoutToShout(trade, shout)

	trade.save()

def ShoutBuy(request, name, text, price, longitude, latitude, tags, shouter, country_code, province_code, address, currency, images = [], date_published = None, stream = None, issss = False, exp_days = None):
	if stream is None:
		stream = shouter.Profile.Stream


	item = item_controller.CreateItem(name,price,images,currency)
	trade = Trade(Text = text, Longitude = longitude, Latitude = latitude, OwnerUser = shouter,
		Type = POST_TYPE_BUY, Item = item, CountryCode = country_code, ProvinceCode = province_code , Address = address, IsSSS = issss)
	trade.save()

	if not PredefinedCity.objects.filter(City = province_code):
		encoded_city = ToSeoFriendly(unicode.lower(unicode(province_code)))
		PredefinedCity(City = province_code, EncodedCity = encoded_city, Country = country_code, Latitude = latitude, Longitude = longitude).save()


	if date_published:
		trade.DatePublished = date_published
		trade.ExpiryDate = exp_days and (date_published + timedelta(days = exp_days)) or None
		trade.save()
	else:
		trade.ExpiryDate = exp_days and datetime.today() + timedelta(days = exp_days) or None
		trade.save()

	stream.PublishShout(trade)
	for tag in ShoutWebsite.controllers.tag_controller.GetOrCreateTags(request, tags, shouter):
		trade.Tags.add(tag)
		tag.Stream.PublishShout(trade)

	if trade:
		trade.StreamsCode = str([f.id for f in trade.Streams.all()])[1:-1]
		trade.save()

	SaveRecolatedShouts(trade, STREAM_TYPE_RECOMMENDED)
	SaveRecolatedShouts(trade, STREAM_TYPE_RELATED)

	event_controller.RegisterEvent(shouter, EVENT_TYPE_SHOUT_REQUEST,trade)
	Logger.log(request, type=ACTIVITY_TYPE_SHOUT_SELL_CREATED, data={ACTIVITY_DATA_SHOUT : trade.id})
	realtime_controller.BindUserToPost(shouter, trade)
	return trade

def ShoutSell(request, name, text, price,  longitude, latitude, tags, shouter, country_code, province_code , address, currency = None , images=[], date_published = None, stream = None, issss = False, exp_days = None):
	if stream is None:
		stream = shouter.Stream

	item = item_controller.CreateItem(name,price,images,currency)
	trade = Trade(Text = text,Longitude = longitude, Latitude = latitude, OwnerUser = shouter.User,
		Type = POST_TYPE_SELL, Item = item , CountryCode = country_code, ProvinceCode = province_code , Address = address, IsSSS = issss)

	if date_published:
		trade.DatePublished = date_published
		trade.ExpiryDate = exp_days and (date_published + timedelta(days = exp_days)) or None
	else:
		trade.ExpiryDate = exp_days and datetime.today() + timedelta(days = exp_days) or None
	trade.save()

	if not PredefinedCity.objects.filter(City = province_code):
		encoded_city = ToSeoFriendly(unicode.lower(unicode(province_code)))
		PredefinedCity(City = province_code, EncodedCity = encoded_city, Country = country_code, Latitude = latitude, Longitude = longitude).save()

	stream.PublishShout(trade)
	for tag in ShoutWebsite.controllers.tag_controller.GetOrCreateTags(request, tags, shouter.User):
		trade.Tags.add(tag)
		tag.Stream.PublishShout(trade)

	if trade:
		trade.StreamsCode = str([f.id for f in trade.Streams.all()])[1:-1]
		trade.save()

	SaveRecolatedShouts(trade, STREAM_TYPE_RECOMMENDED)
	SaveRecolatedShouts(trade, STREAM_TYPE_RELATED)

	event_controller.RegisterEvent(shouter.User, EVENT_TYPE_SHOUT_OFFER,trade)
	Logger.log(request, type=ACTIVITY_TYPE_SHOUT_SELL_CREATED, data={ACTIVITY_DATA_SHOUT : trade.id})
	realtime_controller.BindUserToPost(shouter.User, trade)
	return trade

def GetCurrency(currency_code):
	return Currency.objects.get(Code__iexact = currency_code)

def GetTradeImages(trades):
	images = StoredImage.objects.filter(Shout__pk__in = [trade.pk for trade in trades]).order_by('Image').select_related('Item')
	for i in range(len(trades)):
		trades[i].Item.SetImages([image for image in images if image.Item_id == trades[i].Item.pk])
		images = [image for image in images if image.Item_id != trades[i].Item.pk]
	return trades
from ShoutWebsite import constants, utils
import ShoutWebsite.controllers.email_controller
import ShoutWebsite.controllers.tag_controller
import ShoutWebsite.controllers.stream_controller,event_controller
import ShoutWebsite.controllers.user_controller,business_controller,item_controller
import realtime_controller
from ShoutWebsite.models import GalleryItem, PredefinedCity
from ShoutWebsite.models import Shout, StoredImage, Stream, ShoutWrap, Item, Trade, Experience, Currency, Post, Deal, BusinessProfile, SharedExperience, Comment, GalleryItem