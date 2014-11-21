from django.utils.translation import ugettext_lazy as _
from django.views.decorators.csrf import csrf_exempt
import math
from apps.shoutit.controllers import gallery_controller, item_controller
from apps.shoutit.permissions import PERMISSION_ADD_GALLERY_ITEM, PERMISSION_SHOUT_MORE, PERMISSION_SHOUT_OFFER

from apps.shoutit.tiered_views.renderers import *
from apps.shoutit.tiered_views.validators import *
from apps.shoutit.tiers import *


@cached_view(methods=['GET'],
             tags=[CACHE_TAG_GALLERY],
             json_renderer=lambda request, result, *args: gallery_items_stream_json(request, result))
def galleryItems_stream(request, business_name, page_num=None):
    if not page_num:
        page_num = 1
    else:
        page_num = int(page_num)

    result = ResponseResult()
    business = business_controller.GetBusiness(business_name)
    result.data['items'] = gallery_controller.GetBusinessGalleryItems(business, start_index=DEFAULT_PAGE_SIZE * (page_num - 1),
                                                                      end_index=DEFAULT_PAGE_SIZE * page_num)
    result.data['IsOwner'] = 1 if business.user == request.user else 0
    items_count = len(result.data['items'])
    result.data['pages_count'] = int(math.ceil(items_count / float(DEFAULT_PAGE_SIZE)))
    result.data['is_last_page'] = page_num >= result.data['pages_count']
    return result


@csrf_exempt
@non_cached_view(
    methods=['POST'],
    json_renderer=lambda request, result, business_name: gallery_item_json_renderer(request, result),
    validator=lambda request, business_name: add_gallery_item_validator(request, business_name),
    permissions_required=[PERMISSION_ADD_GALLERY_ITEM]
)
@refresh_cache(tags=[CACHE_TAG_GALLERY])
def add_gallery_item(request, business_name, gallery_id=None):
    result = ResponseResult()
    form = ItemForm(request.POST, request.FILES)
    form.is_valid()

    business = business_controller.GetBusiness(business_name)
    gallery = business.Galleries.all()[0]

    images = []
    if request.POST.has_key('item_images[]'):
        images = request.POST.getlist('item_images[]')
    elif request.POST.has_key('item_images'):
        images = request.POST.getlist('item_images')

    result.data['item'] = gallery_controller.AddItemToGallery(
        request.user,
        gallery,
        form.cleaned_data['name'],
        form.cleaned_data['price'],
        images,
        form.cleaned_data['currency'],
        form.cleaned_data['description'])
    return result


@csrf_exempt
@non_cached_view(
    methods=['POST'],
    json_renderer=lambda request, result, item_id: gallery_item_json_renderer(request, result,
                                                                              message=_('Your item was edited successfully.')),
    validator=lambda request, item_id: object_exists_validator(item_controller.get_item, _('Item does not exist.'), item_id)
)
@refresh_cache(tags=[CACHE_TAG_GALLERY])
def edit_item(request, item_id):
    result = ResponseResult()
    form = ItemForm(request.POST, request.FILES)
    form.is_valid()

    images = []
    if request.POST.has_key('item_images[]'):
        images = request.POST.getlist('item_images[]')
    elif request.POST.has_key('item_images'):
        images = request.POST.getlist('item_images')

    result.data['item'] = item_controller.edit_item(item_id,
                                                    form.cleaned_data['name'],
                                                    form.cleaned_data['price'],
                                                    images,
                                                    form.cleaned_data['currency'],
                                                    form.cleaned_data['description'])
    return result


@csrf_exempt
@non_cached_view(methods=['POST'],
                 json_renderer=lambda request, result, item_id: json_renderer(request, result,
                                                                              success_message=_('You have deleted the item successfully.')),
                 validator=lambda request, item_id: delete_gallery_item_validator(request, item_id),
)
@refresh_cache(tags=[CACHE_TAG_GALLERY])
def delete_gallery_item(request, item_id):
    gallery_controller.DeleteItemFromGallery(item_id)
    result = ResponseResult()
    return result


@non_cached_view(post_login_required=True,
                 validator=lambda request, *args: shout_form_validator(request, ShoutForm),
                 api_renderer=shout_form_renderer_api,
                 html_renderer=lambda request, result, *args: page_html(request, result, 'shout_sell.html', _('Shout Sell')),
                 json_renderer=lambda request, result, *args: json_renderer(request,
                                                                            result,
                                                                            _('Your shout was shouted!'),
                                                                            data=result.data.has_key('shout') and {
                                                                            'next': '/shout/' + result.data['shout'].pk} or {}),
                 permissions_required=[PERMISSION_SHOUT_MORE, PERMISSION_SHOUT_OFFER])
@refresh_cache(tags=[CACHE_TAG_TAGS, CACHE_TAG_STREAMS])
def shout_item(request, item_id):
    result = ResponseResult()

    if request.method == 'POST':
        form = ShoutForm(request.POST, request.FILES)
        form.is_valid()

        if form.cleaned_data['location'] == u'Error':
            result.messages.append(('error', _("Location Not Valid")))
            result.errors.append(RESPONSE_RESULT_ERROR_BAD_REQUEST)
            return result

        latlng = form.cleaned_data['location']
        latitude = float(latlng.split(',')[0].strip())
        longitude = float(latlng.split(',')[1].strip())

        item = item_controller.get_item(item_id)
        gallery_controller.ShoutItem(request, request.user, item,
                                     form.cleaned_data['description'],
                                     longitude,
                                     latitude,
                                     form.cleaned_data['country'],
                                     form.cleaned_data['city'],
                                     form.cleaned_data['address'],
                                     form.cleaned_data['tags'].split(' ')
        )

        result.messages.append(('success', _('Your shout was shouted!')))

        if not request.user.is_active and Shout.objects.filter(OwnerUser=request.user).count() >= settings.MAX_SHOUTS_INACTIVE_USER:
            user_controller.TakePermissionFromUser(request, PERMISSION_SHOUT_MORE)

    else:
        form = ShoutForm()
    result.data['form'] = form
    return result