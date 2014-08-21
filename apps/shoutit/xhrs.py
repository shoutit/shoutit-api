from apps.shoutit.controllers import shout_controller
from apps.shoutit.forms import *
from apps.shoutit.xhr_utils import *

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



def stream_polling(request):
    return HttpResponse()