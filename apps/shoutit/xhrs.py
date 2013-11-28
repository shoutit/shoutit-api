from ShoutWebsite.controllers import shout_controller
from ShoutWebsite.forms import *
from apps.shoutit.xhr_utils import *
#from ShoutWebsite.tasks import poll

@xhr_login_required
def store_shout_sell(request, store_id):
	store = StoreController.GetStore(store_id)
	if request.user != store.Owner:
		return xhr_respond(ENUM_XHR_RESULT.BAD_REQUEST, 'Error! NOT AUTHORIZED')

	form = ShoutForm(request.POST, request.FILES)
	if form.is_valid():
		latlong = form.cleaned_data['location']
		longitude = float(latlong.split(',')[0].strip())
		latitude = float(latlong.split(',')[1].strip())
		shout = shout_controller.ShoutSell(request,
										  form.cleaned_data['name'],
										  form.cleaned_data['description'],
										  form.cleaned_data['image'],
										  form.cleaned_data['price'],
										  longitude,
										  latitude,
										  form.cleaned_data['tags'].split(' '),
										  request.user, store)
		if shout:
			return xhr_respond(ENUM_XHR_RESULT.SUCCESS, 'Your shout was shouted')
		else:
			return xhr_respond(ENUM_XHR_RESULT.FAIL, 'Error!')
	else:
		return xhr_respond(ENUM_XHR_RESULT.BAD_REQUEST, 'You have entered some invalid fields.')

@xhr_login_required
def add_badge_to_user(request, badge_id, user_name):
	try:
		BadgeController.AddToUserBadges(request, badge_id, User.objects.get(username__iexact=user_name))
		return xhr_respond(ENUM_XHR_RESULT.SUCCESS, 'You earned new badge %s.' % badge_id)
	except ObjectDoesNotExist:
		return xhr_respond(ENUM_XHR_RESULT.BAD_REQUEST, 'Badge of id %s was not found.' % badge_id)

@xhr_login_required
def remove_badge_from_user(request, badge_name, user_name):
	try:
		BadgeController.RemoveFromUserBadges(request, badge_name, User.objects.get(username__iexact=user_name))
		return xhr_respond(ENUM_XHR_RESULT.SUCCESS, 'Badge %s was removed from you.' % badge_name)
	except ObjectDoesNotExist:
		return xhr_respond(ENUM_XHR_RESULT.BAD_REQUEST, 'Badge %s was not found.' % badge_name)

html_result = None

def stream_polling(request):
	return HttpResponse()