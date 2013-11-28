from itertools import chain
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.db.models.query_utils import Q
from ShoutWebsite import utils
from ShoutWebsite.constants import STREAM_TYPE_BUSINESS, TOKEN_LONG, TOKEN_TYPE_HTML_EMAIL, TOKEN_TYPE_HTML_EMAIL_BUSINESS_ACTIVATE, FILE_TYPE_BUSINESS_DOCUMENT, TOKEN_TYPE_HTML_EMAIL_BUSINESS_CONFIRM, BUSINESS_CONFIRMATION_STATUS_ACCEPTED, BUSINESS_SOURCE_TYPE_NONE, POST_TYPE_DEAL, POST_TYPE_SELL, POST_TYPE_EVENT, EVENT_TYPE_GALLERY_ITEM
from django.utils.translation import ugettext as _

import ShoutWebsite.controllers.email_controller
from ShoutWebsite.models import Stream, BusinessProfile, ConfirmToken, StoredFile, BusinessConfirmation, Gallery, BusinessSource, Event, Trade, Deal, BusinessCategory, BusinessCreateApplication, PredefinedCity
from ShoutWebsite.permissions import ACTIVATED_BUSINESS_PERMISSIONS
from ShoutWebsite.utils import ToSeoFriendly
import settings

def GetBusiness(username):
	if not isinstance(username,str) and not isinstance(username, unicode):
		return None
	try:
		q = BusinessProfile.objects.filter(User__username__iexact = username).select_related(depth=1)
		if q:
			return q[0]
		else:
			return None
	except ValueError, e:
		return None

def CreateTinyBusinessProfile(name, category, latitude = 0.0, longitude = 0.0, country_code = None, province_code = None, address = None, source_type = BUSINESS_SOURCE_TYPE_NONE, source_id = None):
	username = utils.generateUsername()
	while len(User.objects.filter(username = username).select_related()):
		username = utils.generateUsername()
	password = utils.generateConfirmToken(TOKEN_LONG)
	email = '%s@%s.com' % (username, 'shoutit')

	django_user = User.objects.create_user(username, email, password)
#	django_user.first_name = name

	django_user.is_active = True
	django_user.save()

	stream = Stream(Type = STREAM_TYPE_BUSINESS)
	stream.save()

	cat = None
	if category:
		try:
			cat = BusinessCategory.objects.get(pk = int(category))
		except ObjectDoesNotExist, e:
			cat = None

	bp = BusinessProfile(User = django_user, Category = cat, Stream = stream, Name = name,
						 Latitude = latitude, Longitude = longitude, Country = country_code, City = province_code, Address = address)
	bp.Image = '/static/img/_user_male.png'
	bp.save()

	if not PredefinedCity.objects.filter(City = province_code):
		encoded_city = ToSeoFriendly(unicode.lower(unicode(province_code)))
		PredefinedCity(City = province_code, EncodedCity = encoded_city, Country = country_code, Latitude = latitude, Longitude = longitude).save()

	if source_id is not None:
		source = BusinessSource(Business = bp, Source = source_type, SourceID = source_id)
		source.save()
	return bp

def ClaimTinyBusiness(request, tiny_username, email, phone, website, about = None, documents = []):
	business = GetBusiness(tiny_username)
	if not business:
		return None
	if business.Confirmed:
		return None

	django_user = business.User
	django_user.email = email
	django_user.save()

	business.Phone = phone
	business.Website = website
	business.About = about

	if len(documents):
		confirmation = BusinessConfirmation(User = django_user)
		confirmation.save()
		for document in documents:
			doc = StoredFile(User = django_user, File = document, Type = FILE_TYPE_BUSINESS_DOCUMENT)
			doc.save()
			confirmation.Files.add(doc)
		confirmation.save()
	django_user.save()

	business.save()

	ShoutWebsite.controllers.email_controller.SendBusinessSignupEmail(django_user, email, email)

	return django_user

def SignUpTempBusiness(request, email, password, send_activation = True, business = None):
	if email is None or email == '':
		return None
	username = utils.generateUsername()
	while len(User.objects.filter(username = username).select_related()):
		username = utils.generateUsername()
	django_user = User.objects.create_user(username, email, password)
	app = BusinessCreateApplication(User = django_user, Business = business)
	app.save()

	token = SetTempRegisterToken(django_user, email, TOKEN_LONG, TOKEN_TYPE_HTML_EMAIL_BUSINESS_ACTIVATE)
	
	if email is not None and send_activation:
		ShoutWebsite.controllers.email_controller.SendEmail(email, {
			'name'  : business and business.Name or "New Business",
			'email' : email,
			'link' 	: "http://%s%s" % (settings.SHOUT_IT_DOMAIN, '/'+ token +'/')
		}, "business_temp_registration_email.html", "business_temp_registration_email.txt")

	return django_user

def SetTempRegisterToken(user, email, tokenLength, tokenType):
	token = utils.generateConfirmToken(tokenLength)
	db_token = ConfirmToken.getToken(token)
	while db_token is not None:
		token = utils.generateConfirmToken(tokenLength)
		db_token = ConfirmToken.getToken(token)
	tok = ConfirmToken(Token = token, User = user, Email = email, Type = tokenType)
	tok.save()

	profile = user.BusinessCreateApplication.count() and user.BusinessCreateApplication.all()[0] or None
	if profile:
		profile.LastToken = tok
		profile.save()
	return token

def SignUpBusiness(request, user, name, phone, website, category, about = None,
				   latitude = 0.0, longitude = 0.0, country_code = None, province_code = None, address = None, documents = []):

	try:
		cat = BusinessCategory.objects.get(pk = category)
	except ObjectDoesNotExist, e:
		cat = None

	if user.BusinessCreateApplication.count():
		ba = user.BusinessCreateApplication.all()[0]
		if ba and ba.Business:
			ba.Name = ba.Business.Name
			ba.Category = ba.Business.Category
			ba.Latitude = ba.Business.Latitude
			ba.Longitude = ba.Business.Longitude
			ba.Country = ba.Business.Country
			ba.City = ba.Business.City
			ba.Address = ba.Business.Address
		else:
			ba.Name = name
			ba.Category = cat
			ba.Latitude = latitude
			ba.Longitude = longitude
			ba.Country = country_code
			ba.City = province_code
			ba.Address = address

		ba.Phone = phone
		ba.About = about
		ba.Website = website

	else:
		ba = BusinessCreateApplication(User = user, Category = cat, Name = name, Phone = phone, About = about, Website = website,
					 Latitude = latitude, Longitude = longitude, Country = country_code, City = province_code, Address = address)
	ba.save()

	if not PredefinedCity.objects.filter(City = province_code):
		encoded_city = ToSeoFriendly(unicode.lower(unicode(province_code)))
		PredefinedCity(City = province_code, EncodedCity = encoded_city, Country = country_code, Latitude = latitude, Longitude = longitude).save()


	if len(documents):
		confirmation = BusinessConfirmation(User = user)
		confirmation.save()
		for document in documents:
			doc = StoredFile(User = user, File = document, Type = FILE_TYPE_BUSINESS_DOCUMENT)
			doc.save()
			confirmation.Files.add(doc)
		confirmation.save()
	user.save()

#	bp.Image = '/static/img/_user_male.png'
#	bp.save()
#	business_gallery = Gallery(Description = '', OwnerBusiness = bp)
#	business_gallery.save()

#	TODO log the sign up activity
#	Logger.log(request, type=ACTIVITY_TYPE_SIGN_UP, data={ACTIVITY_DATA_USERNAME : username})
	
	ShoutWebsite.controllers.email_controller.SendBusinessSignupEmail(user, user.email, ba.Name)
	return ba

def EditBusiness(request, username = None, name = None, password = None, email = None, phone=None, image = None,
				 about = None, website = None, latitude = 0.0, longitude = 0.0, country_code = None, province_code = None, address = None):
	if username:
		business = GetBusiness(username)

		if name:
			business.Name = name
		if password:
			business.User.set_password(password)
		if email:
			business.User.email = email
		if phone:
			business.Phone = phone
		if image:
			business.Image = image
		if about:
			business.About = about
		if website:
			business.Website = website
		if latitude != 0.0:
			business.Latitude = latitude
		if longitude != 0.0:
			business.Longitude = longitude
		if country_code:
			business.CountryCode = country_code
		if province_code:
			business.ProvinceCode = province_code
		if address:
			business.Address = address

		business.User.save()
		business.save()

		if not PredefinedCity.objects.filter(City = province_code):
			encoded_city = ToSeoFriendly(unicode.lower(unicode(province_code)))
			PredefinedCity(City = province_code, EncodedCity = encoded_city, Country = country_code, Latitude = latitude, Longitude = longitude).save()


		# TODO log editing activity

		return business
	else:
		return None

def AcceptBusiness(request, username):
	user = username
	if isinstance(username, unicode) or isinstance(username, str):
		if User.objects.filter(username = user).count():
			user = User.objects.filter(username = user)[0]
		else:
			return
	else:
		user = username.User

	profile = user_controller.GetProfile(user)

	if not user.BusinessCreateApplication.count():
		return
	ba = user.BusinessCreateApplication.all()[0]

	if ba.Business and not profile:
		ba.Business.User.password = user.password
		ba.Business.User.email = user.email
		ba.Business.User.is_staff = user.is_staff
		ba.Business.User.is_active = user.is_active
		ba.Business.User.is_superuser = user.is_superuser
		ba.Business.User.last_login = user.last_login
		ba.Business.User.date_joined = user.date_joined

		ba.Business.User.groups = user.groups.all()
		ba.Business.User.user_permissions = user.user_permissions.all()

		ba.User = ba.Business.User
		ba.LastToken = None
		ba.Business.User.BusinessConfirmations = user.BusinessConfirmations.all()
		user.delete()

		ba.Business.User.save()

		user = ba.Business.User

		ba.Business.About = ba.About
		ba.Business.Phone = ba.Phone
		ba.Business.Website = ba.Website
		ba.Business.Confirmed = True
		ba.Business.save()

	elif not ba.Business and not profile:
		stream = Stream(Type = STREAM_TYPE_BUSINESS)
		stream.save()
		bp = BusinessProfile(User = user, Name = ba.Name, Category = ba.Category, Image = "/static/img/_user_male.png",
							About = ba.About, Phone = ba.Phone, Website = ba.Website, Latitude = ba.Latitude, Longitude = ba.Longitude,
							Country = ba.Country, City = ba.City, Address = ba.Address, Stream = stream, Confirmed = True)
		bp.save()
	elif ba.Business:
		ba.Business.Confirmed = True


	ba.Status = BUSINESS_CONFIRMATION_STATUS_ACCEPTED
	ba.save()

	user_controller.GiveUserPermissions(None, ACTIVATED_BUSINESS_PERMISSIONS, user)

	token = user_controller.SetRegisterToken(user, user.email, TOKEN_LONG, TOKEN_TYPE_HTML_EMAIL_BUSINESS_CONFIRM)
	ShoutWebsite.controllers.email_controller.SendBusinessAcceptanceEmail(user.Business, user.email,"http://%s%s" % (settings.SHOUT_IT_DOMAIN, '/'+ token +'/'))

import ShoutWebsite.controllers.user_controller as user_controller