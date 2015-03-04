import time

from django.http import HttpResponseServerError, HttpResponseBadRequest
from django.views.decorators.cache import cache_control
from django.views.decorators.csrf import csrf_exempt
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.http import require_POST

from shoutit.forms import *
from shoutit.models import Category, StoredImage
from shoutit.utils import cloud_upload_file, get_size_url, generate_password, JsonResponse
from shoutit.tiered_views.validators import *
from shoutit.tiered_views.renderers import *
from shoutit.tiers import *
from shoutit.controllers import tag_controller, business_controller, event_controller, item_controller, user_controller, \
    experience_controller


@non_cached_view(html_renderer=index_html, methods=['GET'])
def index(request, browse_type=None):
    result = ResponseResult()
    result.data['browse_type'] = browse_type or 'offers'

    if request.user.is_authenticated():
        city = request.user.profile.city
    else:
        city = DEFAULT_LOCATION['city']

    pre_city = PredefinedCity.objects.get(city=city)

    result.data['browse_city'] = pre_city.city_encoded
    return result


@non_cached_view(html_renderer=lambda request, result: page_html(request, result, 'tos.html', _('Terms of Service')),
                 methods=['GET'])
def tos(request):
    result = ResponseResult()
    return result


@non_cached_view(html_renderer=lambda request, result: page_html(request, result, 'privacy.html', _('Privacy Policy')),
                 methods=['GET'])
def privacy(request):
    result = ResponseResult()
    return result


@non_cached_view(html_renderer=lambda request, result: page_html(request, result, 'rules.html', _('Marketplace Rules')),
                 methods=['GET'])
def rules(request):
    result = ResponseResult()
    return result


@non_cached_view(html_renderer=lambda request, result: page_html(request, result, 'learnmore.html', _('Learn More')),
                 methods=['GET'])
def learnmore(request):
    result = ResponseResult()
    return result


@non_cached_view(methods=['GET'], json_renderer=json_data_renderer)
def hovercard(request):
    type = request.REQUEST['type'] if 'type' in request.REQUEST else None
    name = request.REQUEST['name'] if 'name' in request.REQUEST else None
    data = None
    if name is not None:
        if type == 'user':
            data = user_controller.get_profile(name)
            data.name = data.username
            if request.user.is_authenticated() and request.user.profile == data:
                data.isFollowing = 0
            elif request.user.is_authenticated() and data in request.user.profile.Following.all():
                data.isFollowing = 1
            else:
                data.isFollowing = -1
        elif type == 'tag':
            data = tag_controller.get_tag(name)
            if request.user.is_authenticated() and data in request.user.profile.Interests.all():
                data.isFollowing = 1
            else:
                data.isFollowing = -1

    if data:
        data = {'type': type, 'name': data.name, 'id': data.pk, 'image': str(data.image),
                'listeners': data.Stream.userprofile_set.count(), 'shouts': data.Stream.shouts.count(),
                'isFollowing': data.isFollowing}
    else:
        data = {}
    result = ResponseResult()
    result.data = data
    return result


# todo: better validation and sizing options
@cache_control(public=True, must_revalidate=False)
@non_cached_view(methods=['GET'], login_required=False, validator=profile_picture_validator,
                 html_renderer=thumbnail_response)
def profile_picture(request, profile_type='', size='', tag_name='', username=''):
    if profile_type == 'user' and username == 'me':
        username = request.user.username

    path = ''
    if profile_type == 'user':
        d = user_controller.get_profile(username)
    elif profile_type == 'tag':
        d = tag_controller.get_tag(tag_name)

    if d.image:
        path = d.image
    else:
        path = ''

    result = ResponseResult()
    if size:
        path = get_size_url(path, size)
    result.data['url'] = path

    return result


@cache_control(public=True, must_revalidate=False)
@non_cached_view(methods=['GET'],
                 login_required=False,
                 validator=lambda request, image_id, size: object_exists_validator(StoredImage.objects.get, True,
                                                                                   _('image does not exist.'), pk=image_id),
                 json_renderer=thumbnail_response,
                 html_renderer=thumbnail_response)
def stored_image(request, image_id, size=32):
    image_id = image_id
    image = StoredImage.objects.get(pk=image_id)

    result = ResponseResult()
    path = image.image

    import urlparse

    netloc = urlparse.urlparse(path)[1]

    if netloc != settings.SHOUT_IMAGES_CDN:
        p = os.path.dirname(os.path.normpath(os.sys.modules[settings.SETTINGS_MODULE].__file__))
        path = p + '/ShoutWebsite/' + path

    result.data['picture'] = path

    if size:
        result.data['size'] = (int(size), int(size))
    else:
        result.data['size'] = None
    return result


def modal(request, template=None):
    if not template:
        template = ''
    user = request.user
    fb_la = hasattr(user, 'linked_facebook') and user.linked_facebook or None
    _categories = [category.main_tag and category.main_tag.name or tag_controller.get_or_create_tag(category.name.lower(), None, False).name for
                   category in Category.objects.all().order_by('name').select_related('main_tag')]
    fb_access_token = fb_la.AccessToken if fb_la else None

    if template == 'signin':
        variables = RequestContext(request, {
            'form': LoginForm(),
        })
    elif template == 'signup':
        variables = RequestContext(request, {
            'form': SignUpForm(),
        })
    elif template == 'shout_form':
        variables = RequestContext(request, {
            'form': ShoutForm(),
        })
    elif template == 'shout_buy':
        template = 'shout_form'
        variables = RequestContext(request, {
            'method': 'buy',
            'method_og_name': 'request',
            'form': ShoutForm(),
            'categories': _categories,
            'fb_access_token': fb_access_token
        })
    elif template == 'shout_sell':
        template = 'shout_form'

        variables = RequestContext(request, {
            'method': 'sell',
            'method_og_name': 'offer',
            'form': ShoutForm(),
            'categories': _categories,
            'fb_access_token': fb_access_token
        })
    elif template == 'shout_deal':
        template = 'shout_deal_form'
        variables = RequestContext(request, {
            'form': DealForm(),
        })
    elif template == 'experience':
        template = 'experience_form'
        business = None
        init = {}
        if 'username' in request.GET:
            username = request.GET['username']
            business = business_controller.GetBusiness(username)
            cat = business.Category and business.Category.pk or 0
            init = {'name': business.name, 'category': cat, 'location': str(business.latitude) + ', ' + str(business.longitude),
                    'country': business.country, 'city': business.city, 'address': business.address, 'username': username}
        variables = RequestContext(request, {
            'form': ExperienceForm(initial=init),
            'tiny_business_form': CreateTinyBusinessForm(initial=init),
            'business': business,
            'business_constants': constants.business_source_types,
            'user_constants': constants.user_type_flags,
            'fb_access_token': fb_access_token
        })
    elif template == 'navbar':
        variables = RequestContext(request)
        return render_to_response('modals/navbar.html', variables)
    elif template == 'forgot_password':
        variables = RequestContext(request, {
            'form': RecoverForm(),
        })
    elif template == 'shout_edit':
        shout_id = request.GET['id']
        modify_validation = modify_shout_validator(request, shout_id)
        if modify_validation.valid:
            shout = modify_validation.data['shout']
            variables = RequestContext(request, {
                'method': 'edit',
                'shout': shout,
                'shout_id': request.GET['id'],
                'form': ShoutForm(initial={
                    'price': shout.item.Price,
                    'name': shout.item.name,
                    'tags': ' '.join([tag.name for tag in shout.get_tags()]),
                    'location': '%f,%f' % (shout.latitude, shout.longitude),
                    'description': shout.text,
                    'currency': shout.item.Currency.code
                }),
            })
        else:
            raise Http404()

    elif template == 'shout_item_form' or template == 'edit_item_form':
        item = item_controller.get_item(request.GET['id'])
        if item:
            variables = RequestContext(request, {
                'item_id': request.GET['id'],
                'images': [image.image for image in item.get_images()],
                'form': ShoutForm(initial={
                    'price': item.Price,
                    'name': item.name,
                    'description': item.Description,
                    'currency': item.Currency.code
                })
            })
        else:
            raise Http404()

    elif template == 'experience_edit':
        exp = experience_controller.GetExperience(request.GET['id'], request.user)
        variables = RequestContext(request, {
            'form': ExperienceForm(initial={
                'text': exp.text,
                'state': exp.State
            }),
            'experience_id': request.GET['id']
        })

    elif template == 'report':
        if 'id' in request.GET and 'report_type' in request.GET:
            variables = RequestContext(request, {
                'form': ReportForm(),
                'experience_id': request.GET['id'],
                'report_type': request.GET['report_type']
            })
        else:
            raise Http404()

    else:
        raise Http404()

    return render_to_response('modals/' + template + '_modal.html', variables)


@non_cached_view(methods=['GET'])
def currencies(request):
    result = ResponseResult()
    # todo: use the cache
    result.data['currencies'] = list(Currency.objects.all())
    return result


@non_cached_view(methods=['GET'])
def categories(request):
    result = ResponseResult()
    # todo: use the cache
    result.data['categories'] = list(Category.objects.all().values_list('name', flat=True))
    return result


@non_cached_view(methods=['GET'])
def fake_error(request):
    raise Exception('FAKE ERROR')


def handler500(request):
    f = open('site_off.html')
    content = f.read()
    f.close()
    return HttpResponseServerError(content)


@require_POST
@csrf_exempt
def upload_file(request):
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

    filename = generate_password() + os.path.splitext(filename)[1]
    cloud_file = cloud_upload_file(upload, 'files', filename, is_raw)

    if cloud_file:
        ret_json = {'success': True, 'url': cloud_file.public_uri()}
    else:
        ret_json = {'success': False}
    return JsonResponse(data=ret_json)


@non_cached_view(methods=['GET'], json_renderer=lambda request, result: live_events_json_renderer(request, result))
def live_events(request):
    result = ResponseResult()

    city = request.GET.get('city', DEFAULT_LOCATION['city'])
    try:
        pre_city = PredefinedCity.objects.get(city=city)
    except PredefinedCity.DoesNotExist:
        pre_city = PredefinedCity.objects.get(city=DEFAULT_LOCATION['city'])

    user_country = pre_city.country
    user_city = pre_city.city

    events = []
    if 'timestamp' in request.GET and request.GET['timestamp'] != '':
        timestamp = float(request.GET['timestamp'])
        date = datetime.fromtimestamp(timestamp)
        events = event_controller.GetPublicEventsByLocation(country=user_country, city=user_city, date=date)
    else:
        events = event_controller.GetPublicEventsByLocation(country=user_country, city=user_city)

    events = event_controller.GetDetailedEvents(events)
    result.data['events'] = events
    result.data['count'] = events.count()
    result.data['timestamp'] = time.mktime(datetime.now().timetuple())
    return result


@csrf_exempt
@non_cached_view(methods=['POST'], json_renderer=lambda request, result, *args: json_renderer(request, result),
                 validator=lambda request, event_id: delete_event_validator(request, event_id))
def delete_event(request, event_id):
    result = ResponseResult()
    event_controller.delete_event(event_id)
    return result