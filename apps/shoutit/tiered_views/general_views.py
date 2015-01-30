import time

from django.db.models.aggregates import Count
from django.db.models.query_utils import Q
from django.http import HttpResponseServerError, HttpResponseBadRequest
from django.views.decorators.cache import cache_control
from django.views.decorators.csrf import csrf_exempt
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.http import require_POST

from apps.shoutit.controllers import item_controller
from apps.shoutit.forms import *
from apps.shoutit.models import Category, StoredImage, LinkedFacebookAccount, Message, Conversation, FollowShip, Post
from apps.shoutit.utils import cloud_upload_file, get_size_url, generate_password, JsonResponse
from apps.shoutit.tiered_views.validators import *
from apps.shoutit.tiered_views.renderers import *
from apps.shoutit.tiered_views.views_utils import *
from apps.shoutit.tiers import *
from apps.shoutit.controllers import user_controller


@non_cached_view(html_renderer=index_html, mobile_renderer=index_mobile, api_renderer=shouts_api, methods=['GET'])
def index(request, browse_type=None):
    result = ResponseResult()
    result.data['browse_type'] = browse_type or 'offers'

    if request.user.is_authenticated():
        city = request.user.profile.City
    else:
        city = DEFAULT_LOCATION['city']

    pre_city = PredefinedCity.objects.get(City=city)

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


@cached_view(tags=[CACHE_TAG_TAGS, CACHE_TAG_USERS], methods=['GET'],
             json_renderer=json_data_renderer)
def hovercard(request):
    type = request.REQUEST['type'] if 'type' in request.REQUEST else None
    name = request.REQUEST['name'] if 'name' in request.REQUEST else None
    data = None
    if name is not None:
        if type == 'user':
            data = user_controller.get_profile(name)
            data.Name = data.username
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
        data = {'type': type, 'name': data.Name, 'id': data.pk, 'image': str(data.image),
                'listeners': data.Stream.userprofile_set.count(), 'shouts': data.Stream.Shouts.count(),
                'isFollowing': data.isFollowing}
    else:
        data = {}
    result = ResponseResult()
    result.data = data
    return result


# todo: better validation and sizing options
@cache_control(public=True, must_revalidate=False)
@non_cached_view(methods=['GET'], login_required=False, validator=profile_picture_validator,
                 api_renderer=operation_api,
                 html_renderer=thumbnail_response)
def profile_picture(request, profile_type='', size='', tag_name='', username=''):
    if profile_type == 'user' and username == '@me':
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
                 validator=lambda request, image_id, size: object_exists_validator(StoredImage.objects.get,
                                                                                   _('image does not exist.'), pk=image_id),
                 api_renderer=thumbnail_response,
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
    categories = [category.TopTag and category.TopTag.Name or tag_controller.get_or_create_tag(category.Name, None).Name for
                  category in Category.objects.all().order_by('Name').select_related('TopTag')]
    fb_la = LinkedFacebookAccount.objects.filter(user=request.user).order_by('-pk')[
            :1] if request.user.is_authenticated() else None  # todo onetone
    fb_access_token = fb_la[0].AccessToken if fb_la else None

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
            'categories': categories,
            'fb_access_token': fb_access_token
        })
    elif template == 'shout_sell':
        template = 'shout_form'

        variables = RequestContext(request, {
            'method': 'sell',
            'method_og_name': 'offer',
            'form': ShoutForm(),
            'categories': categories,
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
            init = {'name': business.Name, 'category': cat, 'location': str(business.Latitude) + ', ' + str(business.Longitude),
                    'country': business.Country, 'city': business.City, 'address': business.Address, 'username': username}
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
        if modify_shout_validator(request, shout_id).valid:
            shout = shout_controller.GetPost(shout_id, True, True)
            variables = RequestContext(request, {
                'method': 'edit',
                'shout': shout,
                'shout_id': request.GET['id'],
                'form': ShoutForm(initial={
                    'price': shout.Item.Price,
                    'name': shout.Item.Name,
                    'tags': ' '.join([tag.Name for tag in shout.get_tags()]),
                    'location': '%f,%f' % (shout.Latitude, shout.Longitude),
                    'description': shout.Text,
                    'currency': shout.Item.Currency.Code
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
                    'name': item.Name,
                    'description': item.Description,
                    'currency': item.Currency.Code
                })
            })
        else:
            raise Http404()

    elif template == 'experience_edit':
        exp = experience_controller.GetExperience(request.user, request.GET['id'])
        variables = RequestContext(request, {
            'form': ExperienceForm(initial={
                'text': exp.Text,
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
            variables = RequestContext(request)
    else:
        variables = RequestContext(request)


    return render_to_response('modals/' + template + '_modal.html', variables)


def admin_stats_mobile(request, result):
    if request.user.is_authenticated():
        if request.user.is_staff:
            return page_html(request, result, 'mobile_stats.html')

    return HttpResponseRedirect('/')


@non_cached_view(html_renderer=admin_stats_mobile, mobile_renderer=admin_stats_mobile, methods=['GET'])
def admin_stats(request):
    result = ResponseResult()
    if request.user.is_authenticated():
        if request.user.is_staff:
            result.data['users'] = Profile.objects.all().count()

            users_a = Profile.objects.filter(user__is_active=True).values_list('user__pk')
            result.data['users_a'] = len(users_a)

            users_e = Profile.objects.filter(~Q(user__email__iexact='')).values_list('user_id')  # todo: check
            result.data['users_e'] = len(users_e)

            result.data['sss'] = Profile.objects.filter(user__is_active=True, isSSS=True).count()
            result.data['fb'] = LinkedFacebookAccount.objects.all().values('facebook_id').distinct().count()
            result.data['users_s'] = result.data['users_e'] - result.data['sss'] - result.data['fb']

            result.data['shouts_req'] = Trade.objects.get_valid_trades(types=[POST_TYPE_REQUEST]).count()
            result.data['shouts_ofr'] = Trade.objects.get_valid_trades(types=[POST_TYPE_OFFER]).count()
            result.data['shouts_exp'] = Post.objects.get_valid_posts().filter(Type=POST_TYPE_EXPERIENCE).count()
            result.data['shouts'] = result.data['shouts_req'] + result.data['shouts_ofr'] + result.data['shouts_exp']
            result.data['shouts_a'] = Trade.objects.get_valid_trades([POST_TYPE_REQUEST, POST_TYPE_OFFER]).filter(
                OwnerUser__pk__in=users_a).count()
            result.data['shouts_e'] = Trade.objects.get_valid_trades([POST_TYPE_REQUEST, POST_TYPE_OFFER]).filter(
                OwnerUser__pk__in=users_e).count()
            result.data['shouts_r'] = Trade.objects.get_valid_trades([POST_TYPE_REQUEST, POST_TYPE_OFFER]).filter(OwnerUser__pk__in=users_e,
                                                                                                           IsSSS=False).count()

            result.data['mobiles'] = Profile.objects.filter(~Q(Mobile=None)).count()
            result.data['changed_pic'] = Profile.objects.filter(~Q(
                Image__in=['/static/img/_user_male.png',
                           '/static/img/_user_female.png'])).count()
            result.data['changed_bio'] = Profile.objects.filter(~Q(Bio__iexact='New Shouter!')).count()

            result.data['msgs'] = Message.objects.all().count()
            result.data['convs'] = Conversation.objects.all().count()

            result.data['followships'] = FollowShip.objects.all().count()

            result.data['countries'] = Profile.objects.filter(~Q(user__email__iexact='')).values(
                'Country').annotate(count=Count('Country'))
            for c in result.data['countries']:
                c['Country'] = constants.COUNTRY_ISO[c['Country']]
            result.data['countries'] = sorted(result.data['countries'], key=lambda k: k['Country'])

            # result.data['cities'] = Profile.objects.filter(~Q(user__email__iexact='')).values('City',
        #				'Country').annotate(count=Count('City'))
        #			for c in result.data['cities']:
        #				if c['City'] == '':
        #					c['City'] = 'None'
        #				c['Country'] = constants.COUNTRY_ISO[c['Country']]
        #			result.data['cities'] = sorted(result.data['cities'], key=lambda k: k['Country'])

        #			result.data['fb_contest1_shares'] = FbContest.objects.all().count()
        #			result.data['fb_contest1_users'] = FbContest.objects.all().values('FbId').distinct().count()

    return result


@cached_view(level=CACHE_LEVEL_GLOBAL,
             tags=[CACHE_TAG_CURRENCIES],
             methods=['GET'],
             api_renderer=currencies_api)
def currencies(request):
    result = ResponseResult()
    # todo: use the cache
    result.data['currencies'] = list(Currency.objects.all())
    return result


@non_cached_view(methods=['GET'], api_renderer=categories_list_api)
def categories(request):
    result = ResponseResult()
    # todo: use the cache
    result.data['categories'] = list(Category.objects.all().values_list('Name', flat=True))
    return result


@non_cached_view(methods=['GET'])
def fake_error(request):
    raise Exception('FAKE ERROR')


@non_cached_view(methods=['POST'], json_renderer=json_renderer)
@csrf_exempt
def set_perma(request):
    if request.user.is_authenticated():
        TaggedCache.set('perma|%s|%s' % (request.POST['perma'], request.user.pk), request.POST['value'],
                        timeout=10 * 356 * 24 * 60 * 60)
    elif hasattr(request, 'session'):
        TaggedCache.set('perma|%s|%s' % (request.POST['perma'], request.session.session_key), request.POST['value'],
                        timeout=10 * 356 * 24 * 60 * 60)
    result = ResponseResult()
    return result


@non_cached_view(methods=['POST'], json_renderer=json_renderer)
@csrf_exempt
def set_language(request):
    set_request_language(request, request.POST.get('language', settings.DEFAULT_LANGUAGE_CODE))
    result = ResponseResult()
    return result


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
        pre_city = PredefinedCity.objects.get(City=city)
    except PredefinedCity.DoesNotExist:
        pre_city = PredefinedCity.objects.get(City=DEFAULT_LOCATION['city'])

    user_country = pre_city.Country
    user_city = pre_city.City

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
    event_controller.DeleteEvent(event_id)
    return result