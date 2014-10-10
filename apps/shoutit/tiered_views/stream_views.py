from django.views.decorators.csrf import csrf_exempt
from apps.shoutit.controllers import stream_controller, experience_controller
from apps.shoutit.controllers import user_controller
from apps.shoutit.controllers import notifications_controller
from apps.shoutit.forms import *
from apps.shoutit.models import *
from apps.shoutit.tiered_views.renderers import *
from apps.shoutit.tiered_views.views_utils import get_nearest_points_to_clusters, get_shouts_PointId_inViewPort
from apps.shoutit.tiers import *
from apps.shoutit.utils import kmeans, numberOfClustersBasedOnZoom
from django.core.exceptions import ObjectDoesNotExist


@non_cached_view(html_renderer=browse_html, api_renderer=shouts_api, methods=['GET'])
def browse(request, browse_type, url_encoded_city, browse_category=None):
    result = ResponseResult()
    result.data['notifications'] = []

    result.data['categories'] = Category.objects.all().order_by('Name')
    result.data['predefined_cities'] = PredefinedCity.objects.all()
    # HACK: add dubai
    if not len(result.data['predefined_cities']):
        dubai = PredefinedCity(City='Dubai', EncodedCity='dubai', Country='AE', Approved=True, Latitude=25.2644, Longitude=55.3117)
        dubai.save()
        result.data['predefined_cities'] = PredefinedCity.objects.all()

    if browse_category and browse_category not in [unicode.lower(c.Name) for c in result.data['categories']]:
        result.data['redirect_category'] = True
        return result
    if url_encoded_city not in [c.EncodedCity for c in result.data['predefined_cities']]:
        result.data['redirect_city'] = True
        return result

    result.data['predefined_cities_approved'] = [pdc for pdc in result.data['predefined_cities'] if pdc.Approved ]
    result.data['shouts'] = []
    result.data['count'] = 0
    result.data['browse_type'] = browse_type

    try:
        pre_city = PredefinedCity.objects.get(EncodedCity = url_encoded_city)
    except ObjectDoesNotExist:
        pre_city = PredefinedCity.objects.get(EncodedCity = 'dubai')

    result.data['browse_city'] = pre_city.City
    result.data['browse_city_encoded'] = pre_city.EncodedCity
    result.data['browse_category'] = browse_category

    # save new session for non-users
    if not request.user.is_authenticated():
        request.session['user_lat'] = pre_city.Latitude
        request.session['user_lng'] = pre_city.Longitude
        request.session['user_country'] = pre_city.Country
        request.session['user_city'] = pre_city.City
        request.session['user_city_encoded'] =  pre_city.EncodedCity

# Shouts of Landing Page
    user = request.user if request.user.is_authenticated() else None
    user_country = None
    user_city = result.data['browse_city']
    user_lat = pre_city.Latitude if pre_city and pre_city.City!=user_city else request.session['user_lat']
    user_lng = pre_city.Longitude if pre_city and pre_city.City!=user_city else request.session['user_lng']

    page_num = 1
    tag_ids = []
    types = [POST_TYPE_SELL] if browse_type == 'offers' else [POST_TYPE_BUY] if browse_type == 'requests' else []
    query = None
    category = browse_category

    if browse_type == 'experiences':
        experiences = experience_controller.GetExperiences(user = user, owner_user=None, start_index=DEFAULT_PAGE_SIZE * (page_num - 1),
                                                           end_index=DEFAULT_PAGE_SIZE * page_num, detailed=False, city = user_city)
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
        tag_ids.extend([tag.id for tag in Tag.objects.filter(Category__Name__iexact=category)])

    #TODO session
    if request.session.session_key and TaggedCache.has_key(request.session.session_key + 'shout_ids'):
        TaggedCache.delete(request.session.session_key + 'shout_ids')

    all_shout_ids = stream_controller.GetRankedShoutsIDs(user, order_by, user_country, user_city, user_lat, user_lng, 0,
                                                         DEFAULT_HOME_SHOUT_COUNT, types, query, tag_ids)
    if request.session.session_key:
        TaggedCache.set(request.session.session_key + 'shout_ids', all_shout_ids)

    dict_shout_ids = dict(all_shout_ids)
    shout_ids = [k[0] for k in all_shout_ids if
                 k in all_shout_ids[DEFAULT_PAGE_SIZE * (page_num - 1): DEFAULT_PAGE_SIZE * page_num]]

    if len(shout_ids):
        shouts = stream_controller.GetTradesByIDs(shout_ids)
        for shout in shouts: shout.rank = dict_shout_ids[shout.id]
        shouts.sort(key=lambda shout: shout.rank)
    else:
        shouts = []

    result.data['shouts'] = shouts
    result.data['count'] = len(shouts)

    if request.GET.has_key('zwaar'):
        result.data['flip'] = True
    return result

@cached_view(tags=[CACHE_TAG_STREAMS],
    login_required=False,
    level=CACHE_LEVEL_SESSION,
    api_renderer=shouts_api,
    json_renderer=lambda request, result, page_num: user_stream_json(request, result),
    methods=['GET'])
def index_stream(request, page_num=1):
    result = ResponseResult()

    user = request.user if request.user.is_authenticated() else None

    url_encoded_city = 'url_encoded_city' in request.GET and request.GET['url_encoded_city'] or request.session['user_city_encoded']
    try:
        pre_city = PredefinedCity.objects.get(EncodedCity = url_encoded_city)
    except ObjectDoesNotExist:
        pre_city = PredefinedCity.objects.get(EncodedCity = 'dubai')

    user_country = pre_city.Country
    user_city = pre_city.City
    user_lat = pre_city.Latitude if pre_city and pre_city.City!=user_city else request.session['user_lat']
    user_lng = pre_city.Longitude if pre_city and pre_city.City!=user_city else request.session['user_lng']

    if not page_num:
        page_num = 1
    else:
        page_num = int(page_num)

    tag_ids = request.GET.has_key('tag_ids[]') and request.GET.getlist('tag_ids[]') or []
    types = request.GET.has_key('shout_types[]') and request.GET.getlist('shout_types[]') or []
    query = request.GET.has_key('query') and request.GET['query'] or None
    category = request.GET.has_key('category') and request.GET['category'] or None
    order_by = request.GET.has_key('shouts_order') and int(request.GET['shouts_order']) or 0

    if int(order_by) <= 0:
        order_by = (TIME_RANK_TYPE | FOLLOW_RANK_TYPE | DISTANCE_RANK_TYPE)
    else:
        flag = RankTypeFlag()
        flag.value = int(order_by)
        order_by = flag

    if POST_TYPE_EXPERIENCE in types and len(types) == 1:
        experiences = experience_controller.GetExperiences(user = user, owner_user=None, start_index=DEFAULT_PAGE_SIZE * (page_num - 1),
                                                                                  end_index=DEFAULT_PAGE_SIZE * page_num, city=user_city)
        result.data['count'] = len(experiences)
        result.data['experiences'] = experiences
        return result

    if category is not None:
        if tag_ids is None:
            tag_ids = []
        tag_ids.extend([tag.id for tag in Tag.objects.filter(Category__Name__iexact=category)])

    #TODO: session
    if page_num == 1 and request.session.session_key and TaggedCache.has_key(request.session.session_key + 'shout_ids'):
        TaggedCache.delete(request.session.session_key + 'shout_ids')

    if request.session.session_key and TaggedCache.has_key(request.session.session_key + 'shout_ids'):
        all_shout_ids = TaggedCache.get(request.session.session_key + 'shout_ids')
    else:
        all_shout_ids = stream_controller.GetRankedShoutsIDs(user, order_by, user_country, user_city, user_lat, user_lng, 0,
                                                             DEFAULT_HOME_SHOUT_COUNT, types, query, tag_ids)
        result.data['browse_in'] = user_city
        if request.session.session_key:
            TaggedCache.set(request.session.session_key + 'shout_ids', all_shout_ids)

    dict_shout_ids = dict(all_shout_ids)
    shout_ids = [k[0] for k in all_shout_ids if k in all_shout_ids[DEFAULT_PAGE_SIZE * (page_num - 1): DEFAULT_PAGE_SIZE * page_num]]

    if len(shout_ids):
        shouts = stream_controller.GetTradesByIDs(shout_ids)
        for shout in shouts:
            shout.rank = dict_shout_ids[shout.id]
        shouts.sort(key=lambda x: x.rank)
    else:
        shouts = []

    #todo return info's regarding paging
    result.data['shouts'] = shouts
    result.data['count'] = len(shouts)
    return result


@cached_view(level=CACHE_LEVEL_GLOBAL,
    tags=[CACHE_TAG_STREAMS],
    methods=['GET'],
    api_renderer=shouts_clusters_api)
def load_clusters(request):
    result = ResponseResult()

    topLeftLongitude = float(request.REQUEST['topLeftLongitude'])
    topLeftLatitude = float(request.REQUEST['topLeftLatitude'])
    bottomRightLongitude = float(request.REQUEST['bottomRightLongitude'])
    bottomRightLatitude = float(request.REQUEST['bottomRightLatitude'])

    thirdLongitude = (bottomRightLongitude - topLeftLongitude) / 3.0
    sixthLongitude = (bottomRightLongitude - topLeftLongitude) / 6.0
    thirdLatitude = (bottomRightLatitude - topLeftLatitude) / 3.0
    sixthLatitude = (bottomRightLatitude - topLeftLatitude) / 6.0

    result.data['nw'] = Shout.objects.filter(IsMuted=False, IsDisabled=False,
        Longitude__gte=topLeftLongitude,
        Longitude__lte=topLeftLongitude + thirdLongitude,

        Latitude__gte=topLeftLatitude,
        Latitude__lte=topLeftLatitude + thirdLatitude
    ).count()
    result.data['n'] = Shout.objects.filter(IsMuted=False, IsDisabled=False,
        Longitude__gte=topLeftLongitude + thirdLongitude,
        Longitude__lte=topLeftLongitude + 2 * thirdLongitude,

        Latitude__lte=topLeftLatitude,
        Latitude__gte=topLeftLatitude + thirdLatitude
    ).count()
    result.data['ne'] = Shout.objects.filter(IsMuted=False, IsDisabled=False,
        Longitude__gte=topLeftLongitude + 2 * thirdLongitude,
        Longitude__lte=topLeftLongitude + 3 * thirdLongitude,

        Latitude__lte=topLeftLatitude,
        Latitude__gte=topLeftLatitude + thirdLatitude
    ).count()

    result.data['w'] = Shout.objects.filter(IsMuted=False, IsDisabled=False,
        Longitude__gte=topLeftLongitude,
        Longitude__lte=topLeftLongitude + thirdLongitude,

        Latitude__lte=topLeftLatitude + thirdLatitude,
        Latitude__gte=topLeftLatitude + 2 * thirdLatitude
    ).count()
    result.data['c'] = Shout.objects.filter(IsMuted=False, IsDisabled=False,
        Longitude__gte=topLeftLongitude + thirdLongitude,
        Longitude__lte=topLeftLongitude + 2 * thirdLongitude,

        Latitude__lte=topLeftLatitude + thirdLatitude,
        Latitude__gte=topLeftLatitude + 2 * thirdLatitude
    ).count()
    result.data['e'] = Shout.objects.filter(IsMuted=False, IsDisabled=False,
        Longitude__gte=topLeftLongitude + 2 * thirdLongitude,
        Longitude__lte=topLeftLongitude + 3 * thirdLongitude,

        Latitude__lte=topLeftLatitude + thirdLatitude,
        Latitude__gte=topLeftLatitude + 2 * thirdLatitude
    ).count()

    result.data['sw'] = Shout.objects.filter(IsMuted=False, IsDisabled=False,
        Longitude__gte=topLeftLongitude,
        Longitude__lte=topLeftLongitude + thirdLongitude,

        Latitude__lte=topLeftLatitude + 2 * thirdLatitude,
        Latitude__gte=topLeftLatitude + 3 * thirdLatitude
    ).count()
    result.data['s'] = Shout.objects.filter(IsMuted=False, IsDisabled=False,
        Longitude__gte=topLeftLongitude + thirdLongitude,
        Longitude__lte=topLeftLongitude + 2 * thirdLongitude,

        Latitude__lte=topLeftLatitude + 2 * thirdLatitude,
        Latitude__gte=topLeftLatitude + 3 * thirdLatitude
    ).count()
    result.data['se'] = Shout.objects.filter(IsMuted=False, IsDisabled=False,
        Longitude__gte=topLeftLongitude + 2 * thirdLongitude,
        Longitude__lte=topLeftLongitude + 3 * thirdLongitude,

        Latitude__lte=topLeftLatitude + 2 * thirdLatitude,
        Latitude__gte=topLeftLatitude + 3 * thirdLatitude
    ).count()

    result.data['nw_longitude'] = topLeftLongitude + sixthLongitude
    result.data['nw_latitude'] = topLeftLatitude + sixthLatitude

    result.data['n_longitude'] = topLeftLongitude + sixthLongitude + thirdLongitude
    result.data['n_latitude'] = topLeftLatitude + sixthLatitude

    result.data['ne_longitude'] = topLeftLongitude + sixthLongitude + 2 * thirdLongitude
    result.data['ne_latitude'] = topLeftLatitude + sixthLatitude

    result.data['w_longitude'] = topLeftLongitude + sixthLongitude
    result.data['w_latitude'] = topLeftLatitude + sixthLatitude + thirdLatitude

    result.data['c_longitude'] = topLeftLongitude + sixthLongitude + thirdLongitude
    result.data['c_latitude'] = topLeftLatitude + sixthLatitude + thirdLatitude

    result.data['e_longitude'] = topLeftLongitude + sixthLongitude + 2 * thirdLongitude
    result.data['e_latitude'] = topLeftLatitude + sixthLatitude + thirdLatitude

    result.data['sw_longitude'] = topLeftLongitude + sixthLongitude
    result.data['sw_latitude'] = topLeftLatitude + sixthLatitude + 2 * thirdLatitude

    result.data['s_longitude'] = topLeftLongitude + sixthLongitude + thirdLongitude
    result.data['s_latitude'] = topLeftLatitude + sixthLatitude + 2 * thirdLatitude

    result.data['se_longitude'] = topLeftLongitude + sixthLongitude + 2 * thirdLongitude
    result.data['se_latitude'] = topLeftLatitude + sixthLatitude + 2 * thirdLatitude

    return result

@cached_view(tags=[CACHE_TAG_STREAMS],
    level=CACHE_LEVEL_GLOBAL,
    login_required=False,
    api_renderer=shouts_api,
    json_renderer=shout_xhr,
    methods=['GET'])
def livetimeline(request, id=None):
    result = ResponseResult()
    user_country = request.session['user_country']
    user_city = request.session['user_city']
    user_lat = request.session['user_lat']
    user_lng = request.session['user_lng']

    if id is not None:
        index = stream_controller.GetShoutTimeOrder(int(id), user_country, user_city)
    else:
        index = DEFAULT_PAGE_SIZE
    order_by = TIME_RANK_TYPE

    shouts = []
    if index:
        shout_ids = stream_controller.GetRankedShoutsIDs(None, order_by, user_country, user_city, user_lat, user_lng, 0,index)
#		if len(shout_ids) < DEFAULT_PAGE_SIZE:
#			shout_ids = StreamController.GetRankedShoutsIDs(None, order_by, user_country, None, user_lat, user_lng, 0,
#				index)
        if len(shout_ids):
            shout_ranks = dict(shout_ids)
            shout_ids = [k[0] for k in shout_ids]
            shouts = stream_controller.GetTradesByIDs(shout_ids)
            for shout in shouts:
                shout.rank = shout_ranks[shout.id]
            shouts.sort(key=lambda shout: shout.rank)

    shouts_arr = []

    for shout in shouts:
        variables = {
            'shout': shout
        }
        variables = RequestContext(request, variables)

        shouts_arr.append({'id': shout.id, 'html': render_to_string("shout_brief.html", variables)})
    result.data['shouts'] = shouts_arr
    result.data['count'] = len(shouts_arr)
    return result

@csrf_exempt
@cached_view(tags=[CACHE_TAG_STREAMS],
    level=CACHE_LEVEL_GLOBAL,
    api_renderer=shouts_location_api,
    json_renderer=json_data_renderer)
def load_shouts(request):
    result = ResponseResult()
    shouts, shoutPoints = get_shouts_PointId_inViewPort(float(request.REQUEST[u'DownLeftLat']),
        float(request.REQUEST[u'DownLeftLng']), float(request.REQUEST[u'UpRightLat']),
        float(request.REQUEST[u'UpRightLng']))

    if len(shoutPoints) <= 1:
        if len(shoutPoints) == 1:
            result.data['locations'] = [(str(shoutPoints[0][0]) + ' ' + str(shoutPoints[0][1]))]
            result.data['shoutsId'] = [IntToBase62(shouts[0]['id'])]
            result.data['shoutsTypes'] = [shouts[0]['Type']]
        else:
            result.data['locations'] = []
            result.data['shoutsId'] = []
            result.data['shoutsTypes'] = []
        return result

    k = numberOfClustersBasedOnZoom(int(request.REQUEST[u'Zoom']))
    if k:
        cluster_ids, centroids = kmeans(shoutPoints, min(k, len(shoutPoints)), 100)
        shoutPoints, shoutIds, shoutTypes = get_nearest_points_to_clusters(list(centroids), shoutPoints, shouts)
    else:
        shoutPoints = [str(shout['Latitude']) + ' ' + str(shout['Longitude']) for shout in shouts]
        shoutIds = [IntToBase62(shout['id']) for shout in shouts]
        shoutTypes = [shout['Type'] for shout in shouts]

    result.data['locations'] = shoutPoints
    result.data['shoutsId'] = shoutIds
    result.data['shoutsTypes'] = shoutTypes
    return result