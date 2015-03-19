import json

import os
import re
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.utils.translation import ugettext_lazy as _
from django.http import HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from common.constants import LOCATION_ATTRIBUTES, POST_TYPE_EXPERIENCE
from shoutit.models import Shout, User, DBCLConversation, CLUser, DBUser
from shoutit.controllers.message_controller import get_shout_conversations, ReadConversation, send_message
from shoutit.controllers.stream_controller import get_ranked_stream_shouts
from shoutit.controllers.user_controller import sign_up_sss4, give_user_permissions, take_permission_from_user
from shoutit.controllers import shout_controller
from shoutit.forms import ShoutForm, ReportForm, MessageForm
from shoutit.permissions import PERMISSION_SHOUT_MORE, PERMISSION_SHOUT_REQUEST, PERMISSION_SHOUT_OFFER, INITIAL_USER_PERMISSIONS
from shoutit.tiered_views.renderers import json_renderer, shout_brief_json, object_page_html, json_data_renderer
from shoutit.tiered_views.validators import modify_shout_validator, shout_form_validator, shout_owner_view_validator, edit_shout_validator
from shoutit.tiers import non_cached_view, ResponseResult, RESPONSE_RESULT_ERROR_BAD_REQUEST
from shoutit.utils import shout_link, JsonResponse, JsonResponseBadRequest, cloud_upload_image, random_uuid_str

import logging
logger = logging.getLogger('shoutit.error')


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

    elif request.is_api:
        upload = request
        is_raw = True
        filename = 'WHATEVER.jpg'

    else:
        is_raw = False
        if len(request.FILES) >= 1:
            upload = request.FILES.values()[0]
        else:
            return HttpResponseBadRequest("Bad Upload")
        filename = upload.name

    filename = random_uuid_str() + os.path.splitext(filename)[1]

    if method.startswith('shout_'):
        cloud_image = cloud_upload_image(upload, 'shout_image', filename, is_raw)
    else:
        # TODO: DELETE request.user.profile.image
        cloud_image = cloud_upload_image(upload, method, filename, is_raw)

    if cloud_image:
        ret_json = {'success': True}
        if method == 'user_image':
            profile = request.user.abstract_profile
            profile.image = cloud_image.container.cdn_uri + '/' + cloud_image.name
            profile.save()
        ret_json['url'] = cloud_image.container.cdn_uri + '/' + cloud_image.name
        return JsonResponse(ret_json)
    else:
        return JsonResponseBadRequest({'success': False})


@csrf_exempt
@non_cached_view(methods=['DELETE'], validator=modify_shout_validator,
                 json_renderer=lambda request, result, *args, **kwargs: json_renderer(request, result, _('This shout was deleted.')))
def delete_shout(request, shout_id):
    result = ResponseResult()
    shout = request.validation_result.data['shout']
    shout_controller.delete_post(shout)
    return result


@non_cached_view(methods=['GET'], json_renderer=shout_brief_json)
def load_shout(request, shout_id):
    result = ResponseResult()
    result.data['shout'] = shout_controller.get_post(shout_id)
    return result


@non_cached_view(methods=['POST'], post_login_required=True, validator=modify_shout_validator,
                 json_renderer=lambda request, result, *args, **kwargs:
                 json_renderer(request, result, _('This shout was edited successfully.'), data=result.data))
def renew_shout(request, shout_id):
    shout_id = shout_id
    shout_controller.RenewShout(request, shout_id)
    result = ResponseResult()
    return result


@non_cached_view(post_login_required=True, validator=lambda request, *args, **kwargs: shout_form_validator(request, ShoutForm),
                 permissions_required=[PERMISSION_SHOUT_MORE, PERMISSION_SHOUT_REQUEST],
                 json_renderer=lambda request, result, *args, **kwargs:
                 json_renderer(request, result, _('Your shout was shouted!'),
                               data='shout' in result.data and {'next': shout_link(result.data['shout'])} or {}))
def post_request(request):
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
            latlng = form.cleaned_data['location'].split(',')
            latitude = float(latlng[0].strip())
            longitude = float(latlng[1].strip())
            address = form.cleaned_data['address']

        images = []
        if 'images[]' in request.POST:
            images = request.POST.getlist('images[]', [])
        elif 'images' in request.POST:
            images = request.POST.get('images', [])
        if isinstance(images, basestring):
            images = [images]

        # only from api
        videos = []
        if 'videos' in request.POST:
            videos = request.POST.get('videos', [])

        tags = form.cleaned_data['tags']
        if isinstance(tags, basestring):
            tags = tags.split(' ')

        if not tags:
            result.messages.append(('error', _("tags are invalid")))
            result.errors.append(RESPONSE_RESULT_ERROR_BAD_REQUEST)
            return result

        result.data['shout'] = shout_controller.post_request(name=form.cleaned_data['name'],
                                                          text=form.cleaned_data['description'],
                                                          price=form.cleaned_data['price'],
                                                          latitude=latitude,
                                                          longitude=longitude,
                                                          tags=tags,
                                                          shouter=request.user,
                                                          country=country,
                                                          city=city,
                                                          address=address,
                                                          currency=form.cleaned_data['currency'],
                                                          images=images, videos=videos)

        result.messages.append(('success', _('Your shout was shouted!')))

        if not request.user.is_active and Shout.objects.filter(user=request.user).count() >= settings.MAX_SHOUTS_INACTIVE_USER:
            take_permission_from_user(request, PERMISSION_SHOUT_MORE)

    else:
        form = ShoutForm()
    result.data['form'] = form

    return result


# TODO: better validation for api requests, using other form classes or another validation function
@non_cached_view(post_login_required=True, validator=lambda request, *args, **kwargs: shout_form_validator(request, ShoutForm),
                 permissions_required=[PERMISSION_SHOUT_MORE, PERMISSION_SHOUT_OFFER],
                 json_renderer=lambda request, result, *args, **kwargs:
                 json_renderer(request, result, _('Your shout was shouted!'),
                               data='shout' in result.data and {'next': shout_link(result.data['shout'])} or {}))
def post_offer(request):
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
            latlng = form.cleaned_data['location'].split(',')
            latitude = float(latlng[0].strip())
            longitude = float(latlng[1].strip())
            address = form.cleaned_data['address']

        images = []
        if 'images[]' in request.POST:
            images = request.POST.getlist('images[]', [])
        elif 'images' in request.POST:
            images = request.POST.get('images', [])
        if isinstance(images, basestring):
            images = [images]

        # only from api
        videos = []
        if 'videos' in request.POST:
            videos = request.POST.get('videos', [])

        tags = form.cleaned_data['tags']
        if isinstance(tags, basestring):
            tags = tags.split(' ')

        if not tags:
            result.messages.append(('error', _("tags are invalid")))
            result.errors.append(RESPONSE_RESULT_ERROR_BAD_REQUEST)
            return result

        result.data['shout'] = shout_controller.post_offer(name=form.cleaned_data['name'],
                                                           text=form.cleaned_data['description'],
                                                           price=form.cleaned_data['price'],
                                                           latitude=latitude,
                                                           longitude=longitude,
                                                           tags=tags,
                                                           shouter=request.user,
                                                           country=country,
                                                           city=city,
                                                           address=address,
                                                           currency=form.cleaned_data['currency'],
                                                           images=images, videos=videos)

        result.messages.append(('success', _('Your shout was shouted!')))

        if not request.user.is_active and Shout.objects.filter(user=request.user).count() >= settings.MAX_SHOUTS_INACTIVE_USER:
            take_permission_from_user(request, PERMISSION_SHOUT_MORE)

    else:
        form = ShoutForm()
    result.data['form'] = form
    return result


@non_cached_view(validator=edit_shout_validator,
                 json_renderer=lambda request, result, *args, **kwargs:
                 json_renderer(request, result, _('This shout was edited successfully.'), data=result.data))
def shout_edit(request, shout_id):
    result = ResponseResult()

    shout = request.validation_result.data['shout']
    form = request.validation_result.data['form']
    shouter = shout.user

    latlng = form.cleaned_data['location']
    latitude = float(latlng.split(',')[0].strip())
    longitude = float(latlng.split(',')[1].strip())

    images = []
    if 'images[]' in request.POST:
        images = request.POST.getlist('images[]', [])
    elif 'images' in request.POST:
        images = request.POST.get('images', [])
    if isinstance(images, basestring):
        images = [images]

    # only from api
    videos = []
    if 'videos' in request.POST:
        videos = request.POST.get('videos', [])

    tags = form.cleaned_data['tags']
    if isinstance(tags, basestring):
        tags = tags.split(' ')

    if not tags:
        result.messages.append(('error', _("tags are invalid")))
        result.errors.append(RESPONSE_RESULT_ERROR_BAD_REQUEST)
        return result

    shout = shout_controller.EditShout(shout_id=shout_id, name=form.cleaned_data['name'],
                                       text=form.cleaned_data['description'], price=form.cleaned_data['price'],
                                       latitude=latitude, longitude=longitude, tags=tags,
                                       shouter=shouter, country=form.cleaned_data['country'], city=form.cleaned_data['city'],
                                       address=form.cleaned_data['address'], currency=form.cleaned_data['currency'], images=images)
    result.data['next'] = shout_link(shout)
    return result


@non_cached_view(methods=['GET'], validator=lambda request, shout_id: shout_owner_view_validator(request, shout_id),
                 html_renderer=lambda request, result, shout_id:
                 object_page_html(request, result, 'shout.html', 'title' in result.data and result.data['title'] or '',
                                  'desc' in result.data and result.data['desc'] or '')
)
def shout_view(request, shout_id):
    result = ResponseResult()
    shout_id = shout_id
    if request.user.is_authenticated():
        shout = shout_controller.get_post(shout_id, True, True)
    else:
        shout = shout_controller.get_post(shout_id)

    result.data['shout'] = shout
    result.data['owner'] = (shout.user == request.user or request.user.is_staff)

    if request.user == shout.user:
        shouts = get_ranked_stream_shouts(shout.recommended_stream)
        result.data['shouts_type'] = 'Recommended'
    else:
        shouts = get_ranked_stream_shouts(shout.related_stream)
        result.data['shouts_type'] = 'Related'

    result.data['shouts'] = shouts

    if shout.type == POST_TYPE_EXPERIENCE:
        result.data['title'] = shout.user.username + "'s experience with " + shout.AboutStore.name
    else:
        result.data['title'] = shout.item.name

    result.data['desc'] = shout.text

    if request.user.is_authenticated():
        conversations = get_shout_conversations(shout_id, request.user)
        if not conversations:
            result.data['new_message'] = True
        elif len(conversations) == 1:
            result.data['conversation'] = conversations[0]
            conversations[0].messages = ReadConversation(request.user, conversations[0].pk)
            result.data['conversation_messages'] = conversations[0].messages
            if not result.data['conversation_messages']:
                result.data['new_message'] = True
            result.data['conversation_id'] = conversations[0].pk
        else:
            result.data['conversations'] = conversations

    result.data['form'] = MessageForm()
    result.data['report_form'] = ReportForm()
    result.data['is_fb_og'] = True
    return result


@csrf_exempt
@non_cached_view(json_renderer=json_data_renderer)
def nearby_shouts(request):
    result = ResponseResult()

    # todo: validation
    down_left_lat = float(request.GET.get('down_left_lat', -90))
    down_left_lng = float(request.GET.get('down_left_lng', -180))
    up_right_lat = float(request.GET.get('up_right_lat', 90))
    up_right_lng = float(request.GET.get('up_right_lng', 180))
    zoom = int(request.GET.get('zoom', 1))

    if request.is_api:
        shouts = shout_controller.get_shouts_and_points_in_view_port(down_left_lat, down_left_lng, up_right_lat, up_right_lng, True)
        result.data['shouts'] = shouts
        # todo: clustering for api
        return result

    shouts, shout_points = shout_controller.get_shouts_and_points_in_view_port(down_left_lat, down_left_lng, up_right_lat, up_right_lng)
    # todo: refactor
    if len(shout_points) <= 1:
        if len(shout_points) == 1:
            result.data['locations'] = [(str(shout_points[0][0]) + ' ' + str(shout_points[0][1]))]
            result.data['shout_pks'] = [shouts[0]['pk']]
            result.data['shout_types'] = [shouts[0]['type']]
            result.data['shout_names'] = [shouts[0]['item__name']]
        else:
            result.data['locations'] = []
            result.data['shout_pks'] = []
            result.data['shout_types'] = []
            result.data['shout_names'] = []
        return result

    # todo: cluster-ify this on big data
    shout_points = [str(shout['latitude']) + ' ' + str(shout['longitude']) for shout in shouts]
    shout_pks = [shout['pk'] for shout in shouts]
    shout_types = [shout['type'] for shout in shouts]
    shout_names = [shout['item__name'] for shout in shouts]

    result.data['locations'] = shout_points
    result.data['shout_pks'] = shout_pks
    result.data['shout_types'] = shout_types
    result.data['shout_names'] = shout_names
    return result


@csrf_exempt
def inbound_email(request):
    data = request.POST or request.GET or {}
    if request.method == 'GET':
        print data
        return JsonResponse(data)
    elif request.method == 'POST':
        msg = json.loads(data['mandrill_events'])[0]['msg']
        in_email = msg['email']
        text = msg['text']

        try:
            ref = re.search("\{ref:(.+)\}", text).groups()[0]
        except AttributeError:
            return JsonResponse({'error': "ref wasn't passed in the reply, we can't process the message any further."})

        try:
            text = '\n'.join(text.split('\n> ')[0].splitlines()[:-2])
        except AttributeError:
            return JsonResponse({'error': "we couldn't process the message text."})

        try:
            dbcl_conversation = DBCLConversation.objects.get(ref=ref)
        except DBCLConversation.DoesNotExist, e:
            print e
            return JsonResponse({'error': str(e)})

        from_user = dbcl_conversation.to_user
        to_user = dbcl_conversation.from_user
        shout = dbcl_conversation.shout

        message = send_message(from_user, to_user, shout, text)
        return JsonResponse({'success': True, 'message_id': message.pk})


@csrf_exempt
def shout_sss4(request):
    data = request.json_data
    shout = data['shout']

    try:
        if shout['source'] == 'cl':
            CLUser.objects.get(cl_email=shout['cl_email'])
        elif shout['source'] == 'db':
            DBUser.objects.get(db_link=shout['link'])
        else:
            msg = "Unknown add source: " + shout['source']
            logger.warn(msg)
            return JsonResponseBadRequest({'error': msg})
        msg = "Add already exits. " + shout['link']
        logger.warn(msg)
        return JsonResponseBadRequest({'error': msg})
    except ObjectDoesNotExist:
        pass

    try:
        if shout['source'] == 'cl':
            user = sign_up_sss4(email=shout['cl_email'], lat=shout['lat'], lng=shout['lng'], city=shout['city'], country=shout['country'],
                                dbcl_type='cl')
        if shout['source'] == 'db':
            user = sign_up_sss4(None, lat=shout['lat'], lng=shout['lng'], city=shout['city'], country=shout['country'], dbcl_type='db',
                                db_link=shout['link'])
        give_user_permissions(None, INITIAL_USER_PERMISSIONS, user)
    except Exception, e:
        msg = "User Creation Error: " + str(e)
        logger.error(msg)
        return JsonResponseBadRequest({'error': msg})

    tags = shout['tags']
    if isinstance(tags, basestring):
        tags = tags.split(' ')

    if not tags:
        msg = "Invalid tags: " + shout['tags']
        logger.error(msg)
        return JsonResponseBadRequest({'error': msg})

    try:
        if shout['type'] == 'request':
            shout = shout_controller.post_request(
                name=shout['title'], text=shout['description'], price=float(shout['price']), currency=shout['currency'],
                latitude=float(shout['lat']), longitude=float(shout['lng']), country=shout['country'], city=shout['city'],
                tags=tags, images=shout['images'], shouter=user, is_sss=True, exp_days=settings.MAX_EXPIRY_DAYS_SSS
            )
        elif shout['type'] == 'offer':
            shout = shout_controller.post_offer(
                name=shout['title'], text=shout['description'], price=float(shout['price']), currency=shout['currency'],
                latitude=float(shout['lat']), longitude=float(shout['lng']), country=shout['country'], city=shout['city'],
                tags=tags, images=shout['images'], shouter=user, is_sss=True, exp_days=settings.MAX_EXPIRY_DAYS_SSS
            )

    except Exception, e:
        logger.error(str(e))
        return JsonResponseBadRequest({'error': "Shout Creation Error: " + str(e)})

    return JsonResponse({'success': True})
