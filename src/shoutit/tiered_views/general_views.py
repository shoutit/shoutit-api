import time

from django.http import HttpResponseServerError
from django.views.decorators.cache import cache_control
from django.views.decorators.csrf import csrf_exempt
from django.utils.translation import ugettext_lazy as _

from shoutit.forms import *
from shoutit.models import Category, StoredImage
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