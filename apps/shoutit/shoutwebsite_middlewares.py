from django.dispatch.dispatcher import receiver
from ShoutWebsite.permissions import permissions_changed, ConstantPermission, ANONYMOUS_USER_PERMISSIONS
from ShoutWebsite.models import UserPermission
from ShoutWebsite.tiered_views.views_utils import set_request_language
from ShoutWebsite.utils import ToSeoFriendly
from tagged_cache import TaggedCache
from ShoutWebsite.controllers import facebook_controller
from ShoutWebsite import utils
from ShoutWebsite.controllers import user_controller

class SetLanguageMiddleware(object):
	def process_request(self, request):
		lang = ''
		if request.GET.has_key('lang'):
			lang = request.GET['lang']
		elif request.user.is_authenticated():
			lang = TaggedCache.get('perma|language|%d' % request.user.pk)
		else:
			lang = TaggedCache.get('perma|language|%s' % request.session.session_key)
		if lang:
			set_request_language(request, lang)

class UserPermissionsMiddleware(object):
	@staticmethod
	def attach_permissions_to_request(request):
		if request.user.is_authenticated():
			permissions = TaggedCache.get('perma|permissions|%s' % request.user.username)
			if not permissions:
				permissions = UserPermission.objects.get_user_permissions(request.user)
				permissions = [ConstantPermission.reversed_instances[p] for p in permissions]
				TaggedCache.set('perma|permissions|%s' % request.user.username, permissions, timeout=10 * 356 * 24 * 60 * 60)
			request.user.constant_permissions = permissions
		else:
			request.user.constant_permissions = ANONYMOUS_USER_PERMISSIONS

	def process_request(self, request):
		UserPermissionsMiddleware.attach_permissions_to_request(request)



class FBMiddleware(object):
	def process_request(self, request):
	# Check the requests coming from Facebook
		if request.GET.has_key('code') and request.GET.has_key('fb_source'):
			authResponse = facebook_controller.ExchangeCode(request, request.GET['code'])
			if authResponse:
				facebook_controller.Auth(request, authResponse)
			pass

class UserLocationMiddleware(object):
	def process_request(self, request):
		if not utils.IsSessionHasLocation(request) or request.session.has_key('user_renew_location'):
			if not request.user.is_authenticated():
#				ip = utils.getIP(request)
	#			if not request.session.has_key('user_ip')  or request.session['user_ip'] != ip:
				location_info = utils.getLocationInfoByIP(request)
	#			request.session['user_ip'] = location_info['ip']
				mapped_location = utils.MapWithPredefinedCity(location_info['city'])
				request.session['user_lat'] = mapped_location['latitude']
				request.session['user_lng'] = mapped_location['longitude']
				request.session['user_country'] = mapped_location['country']
				request.session['user_city'] = mapped_location['city']
				request.session['user_city_encoded'] =  mapped_location['city_encoded']
			else:
				profile = user_controller.GetProfile(request.user)
				request.session['user_lat'] = profile and profile.Latitude or 25.2644
				request.session['user_lng'] = profile and profile.Longitude or 55.3117
				request.session['user_country'] = profile and profile.Country or u'AE'
				request.session['user_city'] = profile and profile.City or u'Dubai'
				request.session['user_city_encoded'] =  ToSeoFriendly(unicode.lower(request.session['user_city']))

			if request.session.has_key('user_renew_location'):
				del(request.session['user_renew_location'])

@receiver(permissions_changed)
def refresh_permissions_cache(sender, **kwargs):
	permissions = UserPermission.objects.get_user_permissions(kwargs['request'].user)
	permissions = [ConstantPermission.reversed_instances[p] for p in permissions]
	TaggedCache.set('perma|permissions|%s' % kwargs['request'].user.username, permissions, timeout=10 * 356 * 24 * 60 * 60)
	kwargs['request'].user.constant_permissions = permissions