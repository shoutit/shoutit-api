import os
from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from django.http import HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from apps.shoutit.constants import LOCATION_ATTRIBUTES, POST_TYPE_EXPERIENCE
from apps.shoutit.models import Shout
from apps.shoutit.controllers import shout_controller, stream_controller, user_controller, message_controller
from apps.shoutit.forms import ShoutForm, ReportForm, MessageForm
from apps.shoutit.permissions import PERMISSION_SHOUT_MORE, PERMISSION_SHOUT_REQUEST, PERMISSION_SHOUT_OFFER
from apps.shoutit.tiered_views.renderers import json_renderer, shout_brief_json, shout_brief_api, page_html, shout_form_renderer_api, \
    shout_api, object_page_html, operation_api
from apps.shoutit.tiered_views.validators import modify_shout_validator, shout_form_validator, shout_owner_view_validator, \
    edit_shout_validator
from apps.shoutit.tiers import non_cached_view, cached_view, refresh_cache, CACHE_TAG_STREAMS, ResponseResult, \
    RESPONSE_RESULT_ERROR_BAD_REQUEST, CACHE_TAG_TAGS, CACHE_TAG_USERS, CACHE_TAG_MESSAGES, get_data
from apps.shoutit.utils import generate_password, base62_to_int, shout_link, JsonResponse, JsonResponseBadRequest, cloud_upload_image


@require_POST
@csrf_exempt
def upload_image(request, method=None):
    if request.is_ajax():
        upload = request
        is_raw = True
        try:
            filename = request.GET['qqfile']
        except KeyError:
            return HttpResponseBadRequest("AJAX request not valid")
    else:
        is_raw = False
        if len(request.FILES) == 1:
            upload = request.FILES.values()[0]
        else:
            return HttpResponseBadRequest("Bad Upload")
        filename = upload.name

    if method.startswith('shout_'):
        filename = generate_password() + os.path.splitext(filename)[1]
        cloud_image = cloud_upload_image(upload, 'shout_image', filename, is_raw)
    else:
        # TODO: DELETE request.user.profile.Image
        filename = generate_password() + os.path.splitext(filename)[1]
        cloud_image = cloud_upload_image(upload, method, filename, is_raw)

    if cloud_image:
        ret_json = {'success': True}
        if method == 'user_image':
            profile = user_controller.GetProfile(request.user)
            profile.Image = cloud_image.container.cdn_uri + '/' + cloud_image.name
            profile.save()
        ret_json['url'] = cloud_image.container.cdn_uri + '/' + cloud_image.name
        return JsonResponse(ret_json)
    else:
        return JsonResponseBadRequest({'success': False})



@non_cached_view(methods=['GET', 'DELETE'],
                 validator=modify_shout_validator,
                 api_renderer=operation_api,
                 json_renderer=lambda request, result: json_renderer(request, result, _('This shout was deleted.')))
@refresh_cache(tags=[CACHE_TAG_STREAMS])
def delete_shout(request, id=None):
    if not id:
        id = request.GET[u'id']
        id = base62_to_int(id)
    else:
        id = base62_to_int(id)
    result = ResponseResult()
    shout_controller.DeletePost(id)
    return result


@cached_view(tags=[CACHE_TAG_STREAMS],
             methods=['GET'],
             json_renderer=shout_brief_json,
             api_renderer=shout_brief_api)
def load_shout(request, shout_id):
    result = ResponseResult()
    result.data['shout'] = shout_controller.GetPost(base62_to_int(shout_id))
    return result


@non_cached_view(methods=['POST'],
                 json_renderer=lambda request, result, *args, **kwargs:
                 json_renderer(request, result, _('This shout was edited successfully.'), data=result.data),
                 validator=modify_shout_validator,
                 post_login_required=True)
@refresh_cache(tags=[CACHE_TAG_STREAMS])
def renew_shout(request, shout_id):
    shout_id = base62_to_int(shout_id)
    shout_controller.RenewShout(request, shout_id)
    result = ResponseResult()
    return result


@non_cached_view(post_login_required=True, validator=lambda request, *args, **kwargs: shout_form_validator(request, ShoutForm),
                 html_renderer=lambda request, result, *args: page_html(request, result, 'shout_buy.html', _('Shout Buy')),
                 api_renderer=shout_form_renderer_api,
                 json_renderer=lambda request, result, *args:
                 json_renderer(request, result, _('Your shout was shouted!'),
                               data='shout' in result.data and {'next': shout_link(result.data['shout'])} or {}),
                 permissions_required=[PERMISSION_SHOUT_MORE, PERMISSION_SHOUT_REQUEST])
@refresh_cache(tags=[CACHE_TAG_TAGS, CACHE_TAG_STREAMS, CACHE_TAG_USERS])
def shout_buy(request):
    result = ResponseResult()
    if request.method == 'POST':
        form = ShoutForm(request.POST, request.FILES)
        form.is_valid()

        if getattr(request, 'is_api', False):
            if 'location' in request.POST and all(attr in request.POST['location'] for attr in LOCATION_ATTRIBUTES):
                location = request.POST['location']
                country = location['country']
                city = location['city']
                latitude = float(location['latitude'])
                longitude = float(location['longitude'])
                address = 'address' in location and location['address'] or ''
            else:
                result.messages.append(('error', _("location is invalid")))
                result.errors.append(RESPONSE_RESULT_ERROR_BAD_REQUEST)
                return result

        else:
            if form.cleaned_data['location'] == u'Error':
                result.messages.append(('error', _("location is invalid")))
                result.errors.append(RESPONSE_RESULT_ERROR_BAD_REQUEST)
                return result

            country = form.cleaned_data['country']
            city = form.cleaned_data['city']
            latlong = form.cleaned_data['location'].split(',')
            latitude = float(latlong[0].strip())
            longitude = float(latlong[1].strip())
            address = form.cleaned_data['address']

        images = []
        if 'images[]' in request.POST:
            images = request.POST.getlist('images[]')
        elif 'images' in request.POST:
            try:
                images = request.POST.getlist('images')
            except AttributeError:
                images = request.POST.get('images', [])

        videos = []
        if 'videos[]' in request.POST:
            videos = request.POST.getlist('videos[]')
        elif 'videos' in request.POST:
            try:
                videos = request.POST.getlist('videos')
            except AttributeError:
                videos = request.POST.get('videos', [])

        result.data['shout'] = shout_controller.shout_buy(request,
                                                          name=form.cleaned_data['name'],
                                                          text=form.cleaned_data['description'],
                                                          price=form.cleaned_data['price'],
                                                          latitude=longitude,
                                                          longitude=latitude,
                                                          tags=form.cleaned_data['tags'].split(' '),
                                                          shouter=request.user,
                                                          country_code=country,
                                                          province_code=city,
                                                          address=address,
                                                          currency=form.cleaned_data['currency'],
                                                          images=images, videos=videos)

        result.messages.append(('success', _('Your shout was shouted!')))

        if not request.user.is_active and Shout.objects.filter(OwnerUser=request.user).count() >= settings.MAX_SHOUTS_INACTIVE_USER:
            user_controller.TakePermissionFromUser(request, PERMISSION_SHOUT_MORE)

    else:
        form = ShoutForm()
    result.data['form'] = form

    return result


#TODO: better validation for api requests, using other form classes or another validation function
@non_cached_view(post_login_required=True, validator=lambda request, *args, **kwargs: shout_form_validator(request, ShoutForm),
                 html_renderer=lambda request, result, *args: page_html(request, result, 'shout_sell.html', _('Shout Sell')),
                 api_renderer=shout_form_renderer_api,
                 json_renderer=lambda request, result, *args:
                 json_renderer(request, result, _('Your shout was shouted!'),
                               data='shout' in result.data and {'next': shout_link(result.data['shout'])} or {}),
                 permissions_required=[PERMISSION_SHOUT_MORE, PERMISSION_SHOUT_OFFER])
@refresh_cache(tags=[CACHE_TAG_TAGS, CACHE_TAG_STREAMS, CACHE_TAG_USERS])
def shout_sell(request):
    result = ResponseResult()

    if request.method == 'POST':
        form = ShoutForm(request.POST, request.FILES)
        form.is_valid()

        if getattr(request, 'is_api', False):
            if 'location' in request.POST and all(attr in request.POST['location'] for attr in LOCATION_ATTRIBUTES):
                location = request.POST['location']
                country = location['country']
                city = location['city']
                latitude = float(location['latitude'])
                longitude = float(location['longitude'])
                address = 'address' in location and location['address'] or ''
            else:
                result.messages.append(('error', _("location is invalid")))
                result.errors.append(RESPONSE_RESULT_ERROR_BAD_REQUEST)
                return result

        else:
            if form.cleaned_data['location'] == u'Error':
                result.messages.append(('error', _("location is invalid")))
                result.errors.append(RESPONSE_RESULT_ERROR_BAD_REQUEST)
                return result

            country = form.cleaned_data['country']
            city = form.cleaned_data['city']
            latlong = form.cleaned_data['location'].split(',')
            latitude = float(latlong[0].strip())
            longitude = float(latlong[1].strip())
            address = form.cleaned_data['address']

        images = []
        if 'images[]' in request.POST:
            images = request.POST.getlist('images[]')
        elif 'images' in request.POST:
            try:
                images = request.POST.getlist('images')
            except AttributeError:
                images = request.POST.get('images', [])

        videos = []
        if 'videos[]' in request.POST:
            videos = request.POST.getlist('videos[]')
        elif 'videos' in request.POST:
            try:
                videos = request.POST.getlist('videos')
            except AttributeError:
                videos = request.POST.get('videos', [])

        result.data['shout'] = shout_controller.shout_sell(request,
                                                           name=form.cleaned_data['name'],
                                                           text=form.cleaned_data['description'],
                                                           price=form.cleaned_data['price'],
                                                           latitude=longitude,
                                                           longitude=latitude,
                                                           tags=form.cleaned_data['tags'].split(' '),
                                                           shouter=user_controller.get_profile(request.user.username),
                                                           country_code=country,
                                                           province_code=city,
                                                           address=address,
                                                           currency=form.cleaned_data['currency'],
                                                           images=images, videos=videos)

        result.messages.append(('success', _('Your shout was shouted!')))

        if not request.user.is_active and Shout.objects.filter(OwnerUser=request.user).count() >= settings.MAX_SHOUTS_INACTIVE_USER:
            user_controller.TakePermissionFromUser(request, PERMISSION_SHOUT_MORE)

    else:
        form = ShoutForm()
    result.data['form'] = form
    return result


@non_cached_view(validator=edit_shout_validator,
                 json_renderer=lambda request, result, *args, **kwargs:
                 json_renderer(request, result, _('This shout was edited successfully.'), data=result.data))
@refresh_cache(tags=[CACHE_TAG_TAGS, CACHE_TAG_STREAMS])
def shout_edit(request, shout_id):
    shout_id = base62_to_int(shout_id)
    result = ResponseResult()
    form = ShoutForm(request.POST, request.FILES)
    form.is_valid()
    latlong = form.cleaned_data['location']
    latitude = float(latlong.split(',')[0].strip())
    longitude = float(latlong.split(',')[1].strip())

    shouter = Shout.objects.get(pk=shout_id).OwnerUser

    images = []
    if request.POST.has_key('images[]'):
        images = request.POST.getlist('images[]')
    elif request.POST.has_key('images'):
        images = request.POST.getlist('images')

    shout = shout_controller.EditShout(request, shout_id, form.cleaned_data['name'], form.cleaned_data['description'],
                                       form.cleaned_data['price'],
                                       longitude, latitude, form.cleaned_data['tags'].split(' '),
                                       shouter, form.cleaned_data['country'], form.cleaned_data['city'],
                                       form.cleaned_data['address'], form.cleaned_data['currency'], images)
    result.data['next'] = shout_link(shout)
    return result


@cached_view(tags=[CACHE_TAG_STREAMS, CACHE_TAG_MESSAGES],
             api_renderer=shout_api,
             html_renderer=lambda request, result, shout_id:
             object_page_html(request, result, 'shout.html', 'title' in result.data and result.data['title'] or '',
                              'desc' in result.data and result.data['desc'] or ''),
             methods=['GET'],
             validator=lambda request, shout_id: shout_owner_view_validator(request, base62_to_int(shout_id)))
def shout_view(request, shout_id):
    result = ResponseResult()
    shout_id = base62_to_int(shout_id)
    if request.user.is_authenticated():
        shout = shout_controller.GetPost(shout_id, True, True)
    else:
        shout = shout_controller.GetPost(shout_id)

    result.data['shout'] = shout
    result.data['owner'] = (shout.OwnerUser == request.user or request.user.is_staff)

    if request.user == shout.OwnerUser:
        shouts = stream_controller.GetRankedStreamShouts(shout.RecommendedStream)
        result.data['shouts_type'] = 'Recommended'
    else:
        shouts = stream_controller.GetRankedStreamShouts(shout.RelatedStream)
        result.data['shouts_type'] = 'Related'

    result.data['shouts'] = shouts

    if shout.Type == POST_TYPE_EXPERIENCE:
        result.data['title'] = shout.OwnerUser.username + "'s experience with " + shout.AboutStore.Name
    else:
        result.data['title'] = shout.Item.Name

    result.data['desc'] = shout.Text

    if request.user.is_authenticated():
        conversations = message_controller.get_shout_conversations(shout_id, request.user)
        if not conversations:
            result.data['new_message'] = True
        elif len(conversations) == 1:
            result.data['conversation'] = conversations[0]
            conversations[0].messages = message_controller.ReadConversation(request.user, conversations[0].id)
            result.data['conversation_messages'] = conversations[0].messages
            if not result.data['conversation_messages']:
                result.data['new_message'] = True
            result.data['conversation_id'] = conversations[0].id
        else:
            result.data['conversations'] = conversations

    result.data['form'] = MessageForm()
    result.data['report_form'] = ReportForm()
    result.data['is_fb_og'] = True
    return result