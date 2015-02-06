from math import ceil

from django.template import RequestContext
from django.template.loader import render_to_string
from apps.shoutit.controllers.experience_controller import GetExperiences
from apps.shoutit.controllers.stream_controller import get_trades_by_pks, get_ranked_shouts_ids, GetShoutTimeOrder

from common.constants import POST_TYPE_OFFER, POST_TYPE_REQUEST, DEFAULT_PAGE_SIZE, TIME_RANK_TYPE, FOLLOW_RANK_TYPE, DISTANCE_RANK_TYPE, \
    RankTypeFlag, DEFAULT_HOME_SHOUT_COUNT, POST_TYPE_EXPERIENCE, DEFAULT_LOCATION
from apps.shoutit.models import Category, PredefinedCity, Tag
from apps.shoutit.tiers import non_cached_view, ResponseResult, cached_view, CACHE_TAG_STREAMS, CACHE_LEVEL_GLOBAL
from apps.shoutit.tiered_views.renderers import browse_html, shouts_api, user_stream_json, shout_xhr
from common.tagged_cache import TaggedCache


@non_cached_view(html_renderer=browse_html, methods=['GET'])
def browse(request, browse_type, url_encoded_city, browse_category=None):
    result = ResponseResult()
    result.data['notifications'] = []

    # City
    result.data['predefined_cities'] = PredefinedCity.objects.all()
    try:
        pre_city = PredefinedCity.objects.get(city_encoded=url_encoded_city)
    except PredefinedCity.DoesNotExist:
        pre_city = PredefinedCity.objects.get(city_encoded=DEFAULT_LOCATION['city_encoded'])

    result.data['browse_country'] = pre_city.Country
    result.data['browse_city'] = pre_city.City
    result.data['browse_city_encoded'] = pre_city.city_encoded
    result.data['browse_latitude'] = pre_city.Latitude
    result.data['browse_longitude'] = pre_city.Longitude

    if url_encoded_city not in [c.city_encoded for c in result.data['predefined_cities']]:
        result.data['redirect_city'] = True
        return result

    result.data['predefined_cities_approved'] = [pdc for pdc in result.data['predefined_cities'] if pdc.Approved]
    result.data['shouts'] = []
    result.data['count'] = 0
    result.data['browse_type'] = browse_type

    # Category
    result.data['browse_category'] = browse_category
    result.data['categories'] = Category.objects.all().order_by('Name')
    if browse_category and browse_category not in [unicode.lower(c.Name) for c in result.data['categories']]:
        result.data['redirect_category'] = True
        return result

    # Shouts of Landing Page
    user = request.user if request.user.is_authenticated() else None
    # todo: more cases of default location
    user_country = pre_city.Country
    user_city = pre_city.City
    user_lat = user.profile.Latitude if (request.user.is_authenticated() and user.profile.City == pre_city.City) else pre_city.Latitude
    user_lng = user.profile.Longitude if (request.user.is_authenticated() and user.profile.City == pre_city.City) else pre_city.Longitude

    page_num = 1
    tag_ids = []
    types = [POST_TYPE_OFFER] if browse_type == 'offers' else [POST_TYPE_REQUEST] if browse_type == 'requests' else []
    query = None
    category = browse_category

    if browse_type == 'experiences':
        experiences = GetExperiences(user=user, owner_user=None, start_index=DEFAULT_PAGE_SIZE * (page_num - 1),
                                                           end_index=DEFAULT_PAGE_SIZE * page_num, detailed=False, city=user_city)
        result.data['count'] = len(experiences)
        result.data['experiences'] = experiences
        return result

    order_by = 0 if request.user.is_authenticated() else TIME_RANK_TYPE

    if int(order_by) <= 0:
        order_by = (TIME_RANK_TYPE | FOLLOW_RANK_TYPE | DISTANCE_RANK_TYPE)
    else:
        flag = RankTypeFlag()
        flag.value = int(order_by)
        order_by = flag

    if category is not None:
        if tag_ids is None:
            tag_ids = []
        tag_ids.extend([tag.pk for tag in Tag.objects.filter(Category__Name__iexact=category)])

    #TODO session
    if request.session.session_key and TaggedCache.has_key(request.session.session_key + 'shout_ids'):
        TaggedCache.delete(request.session.session_key + 'shout_ids')

    all_shout_ids = get_ranked_shouts_ids(user, order_by, user_country, user_city, user_lat, user_lng, 0,
                                                         DEFAULT_HOME_SHOUT_COUNT, types, query, tag_ids)
    if request.session.session_key:
        TaggedCache.set(request.session.session_key + 'shout_ids', all_shout_ids)

    dict_shout_ids = dict(all_shout_ids)
    shout_ids = [k[0] for k in all_shout_ids if
                 k in all_shout_ids[DEFAULT_PAGE_SIZE * (page_num - 1): DEFAULT_PAGE_SIZE * page_num]]

    if len(shout_ids):
        shouts = get_trades_by_pks(shout_ids)
        for shout in shouts:
            shout.rank = dict_shout_ids[shout.pk]
        shouts.sort(key=lambda _shout: _shout.rank)
    else:
        shouts = []

    result.data['shouts'] = shouts
    result.data['count'] = len(shouts)

    return result


# todo: check cache!
# @cached_view(tags=[CACHE_TAG_STREAMS], login_required=False, level=CACHE_LEVEL_SESSION, api_renderer=shouts_api,
#              json_renderer=lambda request, result: user_stream_json(request, result), methods=['GET'])
@non_cached_view(methods=['GET'], login_required=False, api_renderer=shouts_api,
                 json_renderer=lambda request, result: user_stream_json(request, result))
def index_stream(request):
    result = ResponseResult()

    user = request.user if request.user.is_authenticated() else None

    city = request.GET.get('city', user.profile.City if request.user.is_authenticated() else DEFAULT_LOCATION['city'])
    try:
        pre_city = PredefinedCity.objects.get(City=city)
    except PredefinedCity.DoesNotExist:
        pre_city = PredefinedCity.objects.get(City=DEFAULT_LOCATION['city'])

    # todo: more cases of default location
    user_country = pre_city.Country
    user_city = pre_city.City
    # todo: better nearby cities based on radius from main city
    user_nearby_cities = PredefinedCity.objects.filter(Country=pre_city.Country)
    user_nearby_cities = [nearby_city.City for nearby_city in user_nearby_cities]
    user_lat = user.profile.Latitude if (request.user.is_authenticated() and user.profile.City == pre_city.City) else pre_city.Latitude
    user_lng = user.profile.Longitude if (request.user.is_authenticated() and user.profile.City == pre_city.City) else pre_city.Longitude

    page_num = int(request.GET.get('page', 1))

    if 'tag_ids[]' in request.GET:
        tag_ids = request.GET.getlist('tag_ids[]')
    else:
        tag_ids = 'tag_ids' in request.GET and request.GET.getlist('tag_ids') or []

    shout_types = request.GET.getlist('shout_types[]', None)
    if not shout_types:
        shout_types = request.GET.getlist('shout_types', [])

    query = request.GET.get('query', None)
    category = request.GET.get('category', None)
    order_by = int(request.GET.get('shouts_order', 0))

    if int(order_by) <= 0:
        order_by = (TIME_RANK_TYPE | FOLLOW_RANK_TYPE | DISTANCE_RANK_TYPE)
    else:
        flag = RankTypeFlag()
        flag.value = int(order_by)
        order_by = flag

    if POST_TYPE_EXPERIENCE in shout_types and len(shout_types) == 1:
        experiences = GetExperiences(user=user, owner_user=None, start_index=DEFAULT_PAGE_SIZE * (page_num - 1),
                                                           end_index=DEFAULT_PAGE_SIZE * page_num, city=user_city)
        result.data['count'] = len(experiences)
        result.data['experiences'] = experiences
        return result

    if category is not None:
        if tag_ids is None:
            tag_ids = []
        tag_ids.extend([tag.pk for tag in Tag.objects.filter(Category__Name__iexact=category)])

    #TODO: session
    if page_num == 1 and request.session.session_key and TaggedCache.has_key(request.session.session_key + 'shout_ids'):
        TaggedCache.delete(request.session.session_key + 'shout_ids')

    if request.session.session_key and TaggedCache.has_key(request.session.session_key + 'shout_ids'):
        all_shout_ids = TaggedCache.get(request.session.session_key + 'shout_ids')
    else:
        all_shout_ids = get_ranked_shouts_ids(user, order_by, user_country, user_city, user_lat, user_lng, 0, DEFAULT_HOME_SHOUT_COUNT,
                                              shout_types, query, tag_ids, nearby_cities=user_nearby_cities)
        result.data['browse_in'] = user_city
        if request.session.session_key:
            TaggedCache.set(request.session.session_key + 'shout_ids', all_shout_ids)

    dict_shout_ids = dict(all_shout_ids)
    shout_ids = [k[0] for k in all_shout_ids if k in all_shout_ids[DEFAULT_PAGE_SIZE * (page_num - 1): DEFAULT_PAGE_SIZE * page_num]]

    if len(shout_ids):
        shouts = get_trades_by_pks(shout_ids)
        for shout in shouts:
            shout.rank = dict_shout_ids[shout.pk]
        shouts.sort(key=lambda x: x.rank)
    else:
        shouts = []

    result.data['shouts'] = shouts
    result.data['count'] = len(shouts)
    result.data['city'] = user_city

    result.data['pages_count'] = int(ceil(len(all_shout_ids) / float(DEFAULT_PAGE_SIZE)))
    result.data['is_last_page'] = page_num >= result.data['pages_count']

    return result


@non_cached_view(methods=['GET'], login_required=False, api_renderer=shouts_api, json_renderer=shout_xhr)
def livetimeline(request, pk=None):
    result = ResponseResult()

    city = request.user.profile.City if request.user.is_authenticated() else DEFAULT_LOCATION['city']
    pre_city = PredefinedCity.objects.get(City=city)
    user_country = pre_city.Country
    user_city = pre_city.City
    user_lat = pre_city.Latitude
    user_lng = pre_city.Longitude

    if pk is not None:
        index = GetShoutTimeOrder(pk, user_country, user_city)
    else:
        index = DEFAULT_PAGE_SIZE
    order_by = TIME_RANK_TYPE

    shouts = []
    if index:
        shout_ids = get_ranked_shouts_ids(None, order_by, user_country, user_city, user_lat, user_lng, 0, index)
        if len(shout_ids):
            shout_ranks = dict(shout_ids)
            shout_ids = [k[0] for k in shout_ids]
            shouts = get_trades_by_pks(shout_ids)
            for shout in shouts:
                shout.rank = shout_ranks[shout.pk]
            shouts.sort(key=lambda _shout: _shout.rank)

    shouts_arr = []

    for shout in shouts:
        variables = {
            'shout': shout
        }
        variables = RequestContext(request, variables)

        shouts_arr.append({'id': shout.pk, 'html': render_to_string("shout_brief.html", variables)})
    result.data['shouts'] = shouts_arr
    result.data['count'] = len(shouts_arr)
    return result
