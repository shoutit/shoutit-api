import mimetypes
import cloudfiles
import math
from django.utils.translation import ugettext_lazy as _
from django.http import HttpResponseBadRequest
from django.template import loader
from django.views.decorators.csrf import csrf_exempt
import time
from apps.shoutit.controllers import shout_controller, stream_controller, comment_controller, gallery_controller
from apps.shoutit.controllers import user_controller , comment_controller
from apps.shoutit.controllers import message_controller,business_controller
from apps.shoutit.forms import *
from apps.shoutit.models import *
from apps.shoutit.permissions import PERMISSION_SHOUT_MORE, PERMISSION_SHOUT_REQUEST, PERMISSION_SHOUT_OFFER, PERMISSION_POST_EXPERIENCE, PERMISSION_SHARE_EXPERIENCE, PERMISSION_COMMENT_ON_POST
from apps.shoutit.tiered_views.general_views import get_cloud_connection
from apps.shoutit.tiered_views.renderers import *
from apps.shoutit.tiered_views.validators import *
from apps.shoutit.tiers import *
from apps.shoutit.utils import GeneratePassword, getLocationInfoBylatlng
from apps.shoutit.constants import *

cloud_connection = None


def cloud_save_upload(uploaded, container_name, filename, raw_data):
    try:
        cf = get_cloud_connection().cloudfiles
        container = cf.get_container(container_name)
        data = ''
        if raw_data:
            data = uploaded.body
        else:
            for c in uploaded.chunks():
                data += c
        import Image
        import StringIO

        filename = os.path.splitext(filename)[0] + '.jpg'
        buff = StringIO.StringIO()
        buff.write(data)
        buff.seek(0)
        image = Image.open(buff)
        if container.name == 'user_image':
            width, height = image.size
            if width != height:
                box = (0, 0, min(width, height), min(width, height))
                image = image.crop(box)
                image.format = "JPEG"
            image.thumbnail((220, 220), Image.ANTIALIAS)
        else:
            image.thumbnail((800, 600), Image.ANTIALIAS)
        buff = StringIO.StringIO()
        image.save(buff, format="JPEG", quality=60)
        buff.seek(0)

        obj = container.store_object(obj_name=filename, data=buff.buf, content_type=mimetypes.guess_type(filename))

        if container.name == 'user_image':
            utils.make_image_thumbnail(obj.container.cdn_uri + '/' + obj.name, 95, 'user_image')
            utils.make_image_thumbnail(obj.container.cdn_uri + '/' + obj.name, 32, 'user_image')

        return obj
    except Exception, e:
        raise Http404(e.message)
    return None


def cloud_upload(request, method=None):
    if request.method == "POST":
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
                raise Http404("Bad Upload")
            filename = upload.name
        import os

        if method.startswith('shout_'):
            filename = GeneratePassword() + os.path.splitext(filename)[1]
            cloud_file = cloud_save_upload(upload, 'shout_image', filename, is_raw)
        else:
            #TODO: DELETE request.user.Profile.Image
            filename = GeneratePassword() + os.path.splitext(filename)[1]
            cloud_file = cloud_save_upload(upload, method, filename, is_raw)
        import json

        if cloud_file:
            ret_json = {'success': True}
            if method == 'user_image':
                profile = user_controller.GetProfile(request.user)
                profile.Image = cloud_file.container.cdn_uri + '/' + cloud_file.name
                profile.save()
            ret_json['url'] = cloud_file.container.cdn_uri + '/' + cloud_file.name
        else:
            ret_json = {'success': False}
        return HttpResponse(json.dumps(ret_json))

@non_cached_view(methods=['GET', 'DELETE'],
    validator=modify_shout_validator,
    api_renderer=operation_api,
    json_renderer=lambda request, result, *args, **kwargs: json_renderer(request, result, _('This shout was deleted.')))
@refresh_cache(tags=[CACHE_TAG_STREAMS])
def delete_shout(request, id=None):
    if not id:
        id = request.GET[u'id']
        id = Base62ToInt(id)
    else:
        id = Base62ToInt(id)
    result = ResponseResult()
    shout_controller.DeletePost(id)
    return result

@cached_view(tags=[CACHE_TAG_STREAMS],
    methods=['GET'],
    json_renderer = shout_brief_json,
    api_renderer = shout_brief_api)
def load_shout(request,shout_id):
    result = ResponseResult()
#	request.GET[u'shoutId']
    result.data['shout'] = shout_controller.GetPost(Base62ToInt(shout_id))
    return result

@non_cached_view(methods=['POST'],
    json_renderer=lambda request, result, *args, **kwargs: json_renderer(request, result,
        _('This shout was edited successfully.'), data=result.data),
    validator=modify_shout_validator,
    post_login_required=True)
@refresh_cache(tags=[CACHE_TAG_STREAMS])
def renew_shout(request, shout_id):
    shout_id = utils.Base62ToInt(shout_id)
    shout_controller.RenewShout(request, shout_id)
    #streams = ShoutController.GetStreamAffectedByShout(shout_id)
    #[refresh_cache_dynamically([CACHE_TAG_STREAMS.make_dynamic(stream)]) for stream in streams]
    result = ResponseResult()
    return result

@non_cached_view(post_login_required=True,
    validator=lambda request, *args, **kwargs: shout_form_validator(request, ShoutForm),
    html_renderer=lambda request, result: page_html(request, result, 'shout_buy.html', _('Shout Buy')),
    api_renderer=shout_form_renderer_api,
    json_renderer=lambda request, result: json_renderer(request,
        result,
        _('Your shout was shouted!'),
        data=result.data.has_key('shout') and {'next': utils.ShoutLink(result.data['shout'])} or {}),
    permissions_required = [PERMISSION_SHOUT_MORE, PERMISSION_SHOUT_REQUEST])
@refresh_cache(tags=[CACHE_TAG_TAGS, CACHE_TAG_STREAMS,CACHE_TAG_USERS])
def shout_buy(request):
    result = ResponseResult()
    if request.method == 'POST':
        form = ShoutForm(request.POST, request.FILES)
        form.is_valid()

        if form.cleaned_data['location'] == u'Error':
            result.messages.append(('error', _("Location Not Valid")))
            result.errors.append(RESPONSE_RESULT_ERROR_BAD_REQUEST)
            return result

        latlong = form.cleaned_data['location']
        latitude = float(latlong.split(',')[0].strip())
        longitude = float(latlong.split(',')[1].strip())

        images = []
        if request.POST.has_key('shout_images[]'):
            images = request.POST.getlist('shout_images[]')
        elif request.POST.has_key('shout_images'):
            images = request.POST.getlist('shout_images')
        result.data['shout'] = shout_controller.ShoutBuy(request, form.cleaned_data['name'],
            form.cleaned_data['description'],
            form.cleaned_data['price'],
            longitude,
            latitude,
            form.cleaned_data['tags'].split(' '),
            request.user,
            form.cleaned_data['country'],
            form.cleaned_data['city'],
            form.cleaned_data['address'],
            form.cleaned_data['currency'],
            images=images)

        result.messages.append(('success', _('Your shout was shouted!')))

        if not request.user.is_active and Shout.objects.filter(OwnerUser = request.user).count() >= settings.MAX_SHOUTS_INACTIVE_USER:
            user_controller.TakePermissionFromUser(request, PERMISSION_SHOUT_MORE)

        #streams = ShoutController.GetStreamAffectedByShout(result.data['shout'])
        #[refresh_cache_dynamically([CACHE_TAG_STREAMS.make_dynamic(stream)]) for stream in streams]
    else:
        form = ShoutForm()
    result.data['form'] = form

    return result

@non_cached_view(validator=edit_shout_validator,
    json_renderer=lambda request, result, *args, **kwargs: json_renderer(request, result,
        _('This shout was edited successfully.'), data=result.data))
@refresh_cache(tags=[CACHE_TAG_TAGS, CACHE_TAG_STREAMS])
def shout_edit(request, shout_id):
    shout_id = utils.Base62ToInt(shout_id)
    result = ResponseResult()
    form = ShoutForm(request.POST, request.FILES)
    form.is_valid()
    latlong = form.cleaned_data['location']
    latitude = float(latlong.split(',')[0].strip())
    longitude = float(latlong.split(',')[1].strip())

    shouter = Shout.objects.get(pk=shout_id).OwnerUser

    images = []
    if request.POST.has_key('shout_images[]'):
        images = request.POST.getlist('shout_images[]')
    elif request.POST.has_key('shout_images'):
        images = request.POST.getlist('shout_images')

    shout = shout_controller.EditShout(request, shout_id, form.cleaned_data['name'], form.cleaned_data['description'],
        form.cleaned_data['price'],
        longitude, latitude, form.cleaned_data['tags'].split(' '),
        shouter, form.cleaned_data['country'], form.cleaned_data['city'],
        form.cleaned_data['address'], form.cleaned_data['currency'], images)
    result.data['next'] = utils.ShoutLink(shout)
    #streams = ShoutController.GetStreamAffectedByShout(shout)
    #[refresh_cache_dynamically([CACHE_TAG_STREAMS.make_dynamic(stream)]) for stream in streams]
    return result


@non_cached_view(post_login_required=True,
    validator=lambda request, *args : shout_form_validator(request, ShoutForm),
    api_renderer=shout_form_renderer_api,
    html_renderer=lambda request, result, *args : page_html(request, result, 'shout_sell.html', _('Shout Sell')),
    json_renderer=lambda request, result, *args : json_renderer(request,
        result,
        _('Your shout was shouted!'),
        data=result.data.has_key('shout') and {'next': utils.ShoutLink(result.data['shout'])} or {}),
    permissions_required = [PERMISSION_SHOUT_MORE, PERMISSION_SHOUT_OFFER])
@refresh_cache(tags=[CACHE_TAG_TAGS, CACHE_TAG_STREAMS,CACHE_TAG_USERS])
def shout_sell(request):
    result = ResponseResult()

    if request.method == 'POST':
        form = ShoutForm(request.POST, request.FILES)
        form.is_valid()

        if form.cleaned_data['location'] == u'Error':
            result.messages.append(('error', _("Location Not Valid")))
            result.errors.append(RESPONSE_RESULT_ERROR_BAD_REQUEST)
            return result

        latlong = form.cleaned_data['location']
        latitude = float(latlong.split(',')[0].strip())
        longitude = float(latlong.split(',')[1].strip())


        images = []
        if request.POST.has_key('shout_images[]'):
            images = request.POST.getlist('shout_images[]')
        elif request.POST.has_key('shout_images'):
            images = request.POST.getlist('shout_images')

        result.data['shout'] = shout_controller.ShoutSell(request,
            form.cleaned_data['name'],
            form.cleaned_data['description'],
            form.cleaned_data['price'],
            longitude,
            latitude,
            form.cleaned_data['tags'].split(' '),
            user_controller.GetUser(request.user.username),
            form.cleaned_data['country'],
            form.cleaned_data['city'],
            form.cleaned_data['address'],
            form.cleaned_data['currency'],
            images=images)

        result.messages.append(('success', _('Your shout was shouted!')))

        if not request.user.is_active and Shout.objects.filter(OwnerUser = request.user).count() >= settings.MAX_SHOUTS_INACTIVE_USER:
            user_controller.TakePermissionFromUser(request, PERMISSION_SHOUT_MORE)

        #streams = ShoutController.GetStreamAffectedByShout(result.data['shout'])
        #[refresh_cache_dynamically([CACHE_TAG_STREAMS.make_dynamic(stream)]) for stream in streams]
    else:
        form = ShoutForm()
    result.data['form'] = form
    return result

@cached_view(tags=[CACHE_TAG_STREAMS, CACHE_TAG_MESSAGES],
    api_renderer=shout_api,
    html_renderer=lambda request, result, shout_id: object_page_html(request, result, 'shout.html',
        result.data.has_key('title') and result.data['title'] or '',
        result.data.has_key('desc') and result.data['desc'] or ''),
    methods=['GET'],
    validator=lambda request, shout_id: shout_owner_view_validator(request, Base62ToInt(shout_id)))
def shout_view(request, shout_id):
    result = ResponseResult()
    shout_id = Base62ToInt(shout_id)
    if request.user.is_authenticated():
        #shout = get_data([CACHE_TAG_STREAMS.make_dynamic(request.user.Profile.Stream)], lambda: ShoutController.GetShout(shout_id, True, True))
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
        result.data['title'] = shout.OwnerUser.username + '\'s experience with ' + shout.AboutStore.Name
    else:
        result.data['title'] = shout.Item.Name

    result.data['desc'] = shout.Text

    if request.user.is_authenticated():
        conversations = message_controller.GetShoutConversations(shout_id, request.user)
        if not conversations:
            result.data['new_message'] = True
        elif len(conversations) == 1:
            result.data['conversation'] = conversations[0]
            conversations[0].messages = get_data([CACHE_TAG_MESSAGES.make_dynamic(request.user)],
                lambda: message_controller.ReadConversation(request.user, conversations[0].id))
            result.data['conversation_messages'] = conversations[0].messages
            if not result.data['conversation_messages']:
                result.data['new_message'] = True
            result.data['conversation_id'] = conversations[0].id
        else:
            #result.data['conversations'] = get_data([CACHE_TAG_MESSAGES.make_dynamic(request.user)], lambda: conversations)
            result.data['conversations'] = conversations

    result.data['form'] = MessageForm()
    result.data['report_form'] = ReportForm()
    result.data['is_fb_og'] = True
    return result