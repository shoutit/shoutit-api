import math
from django.utils.translation import ugettext_lazy as _
from apps.shoutit.controllers import stream_controller
from apps.shoutit.controllers import tag_controller
from apps.shoutit.forms import *
from apps.shoutit.models import *
from apps.shoutit.permissions import PERMISSION_FOLLOW_TAG
from apps.shoutit.tiered_views.renderers import *
from apps.shoutit.tiered_views.validators import *
from apps.shoutit.tiers import *
from apps.shoutit.constants import *
from apps.shoutit.templatetags.template_filters import thumbnail


@non_cached_view(methods=['GET', 'POST'],
                 login_required=True,
                 api_renderer=operation_api,
                 json_renderer=lambda request, result, tag_name:
                 json_renderer(request, result, _('You are now listening to shouts about %(tag_name)s.') % {'tag_name': tag_name}),
                 validator=lambda request, tag_name:
                 object_exists_validator(tag_controller.get_tag, _('Tag %(tag_name)s does not exist.') % {'tag_name': tag_name}, tag_name),
                 permissions_required=[PERMISSION_FOLLOW_TAG])
@refresh_cache(tags=[CACHE_TAG_STREAMS, CACHE_TAG_USERS, CACHE_TAG_TAGS])
def start_listening_to_tag(request, tag_name):
    result = ResponseResult()
    tag = request.validation_result.data

    stream_controller.listen_to_stream(request.user, tag.stream2)
    # todo: add tracking event

    # todo: remove old streams
    tag_controller.AddToUserInterests(request, tag_name, request.user)

    return result


@non_cached_view(methods=['GET', 'DELETE'],
                 login_required=True,
                 api_renderer=operation_api,
                 json_renderer=lambda request, result, tag_name:
                 json_renderer(request, result, _('You are no longer listening to shouts about %(tag_name)s.') % {'tag_name': tag_name},
                               success_message_type='info'),
                 validator=lambda request, tag_name:
                 object_exists_validator(tag_controller.get_tag, _('Tag %(tag_name)s does not exist.') % {'tag_name': tag_name}, tag_name))
@refresh_cache(tags=[CACHE_TAG_STREAMS, CACHE_TAG_USERS, CACHE_TAG_TAGS])
def stop_listening_to_tag(request, tag_name):
    result = ResponseResult()
    tag = request.validation_result.data

    stream_controller.remove_listener_from_stream(request.user, tag.stream2)
    # todo: add tracking event

    # todo: [listen] replace
    tag_controller.RemoveFromUserInterests(request, tag_name, request.user)

    return result


@cached_view(level=CACHE_LEVEL_GLOBAL,
             tags=[CACHE_TAG_TAGS],
             api_renderer=tags_api,
             json_renderer=json_data_renderer,
             methods=['GET'])
def search_tag(request):
    limit = 6
    query = request.GET.get('query', '')
    tags = list(tag_controller.SearchTags(query, limit))
    result = ResponseResult()
    result.data = tags
    return result


@non_cached_view(methods=['GET'],
                 json_renderer=json_data_renderer)
@refresh_cache(tags=[CACHE_TAG_TAGS])
def set_tag_parent(request):
    result = ResponseResult()
    tag_controller.setTagParent(request.GET[u'child_id'], request.GET[u'parent_name'])
    return result


@cached_view(level=CACHE_LEVEL_SESSION,
             tags=[CACHE_TAG_TAGS],
             json_renderer=json_data_renderer,
             methods=['GET'])
def top_tags(request):
    result = ResponseResult()

    city = request.GET.get('city', DEFAULT_LOCATION['city'])

    try:
        pre_city = PredefinedCity.objects.get(City=city)
    except PredefinedCity.DoesNotExist:
        pre_city = PredefinedCity.objects.get(City=DEFAULT_LOCATION['city'])

    user_country = pre_city.Country
    user_city = pre_city.City
    profile = user_controller.GetProfile(request.user)
    result.data['top_tags'] = tag_controller.GetTopTags(10, user_country, user_city)
    if request.user.is_authenticated() and isinstance(profile, Profile):
        user_interests = profile.Interests.all().values_list('Name')
        for tag in result.data['top_tags']:
            tag['is_listening'] = (tag['Name'], ) in user_interests
    else:
        for tag in result.data['top_tags']:
            tag['is_listening'] = False
    return result


@cached_view(level=CACHE_LEVEL_SESSION,
             tags=[CACHE_TAG_STREAMS, CACHE_TAG_TAGS],
             methods=['GET'],
             api_renderer=shouts_api,
             json_renderer=lambda request, result, tag_name, *args: user_stream_json(request, result),
             validator=lambda request, tag_name, *args, **kwargs: object_exists_validator(tag_controller.get_tag,
                                                                                          _('Tag %(tag_name)s does not exist.') % {'tag_name': tag_name}, tag_name))
def tag_stream(request, tag_name):
    result = ResponseResult()
    tag = request.validation_result.data

    page_num = int(request.GET.get('page', 1))
    start_index = DEFAULT_PAGE_SIZE * (page_num - 1)
    end_index = DEFAULT_PAGE_SIZE * page_num

    city = request.user.profile.City if request.user.is_authenticated() else DEFAULT_LOCATION['city']
    pre_city = PredefinedCity.objects.get(City=city)
    user_country = pre_city.Country
    user_city = pre_city.City

    result.data['shouts_count'] = stream_controller.get_stream_shouts_count(tag.Stream)
    result.data['shouts'] = stream_controller.get_stream_shouts(tag.Stream, start_index, end_index, country=user_country, city=user_city)

    result.data['pages_count'] = int(math.ceil(result.data['shouts_count'] / float(DEFAULT_PAGE_SIZE)))

    result.data['is_last_page'] = page_num >= result.data['pages_count']
    result.data['browse_in'] = user_city
    return result


@cached_view(level=CACHE_LEVEL_SESSION,
             tags=[CACHE_TAG_TAGS, CACHE_TAG_STREAMS],
             api_renderer=tag_api,
             html_renderer=lambda request, result, tag_name: object_page_html(request, result, 'tag_profile.html', tag_name),
             methods=['GET'],
             validator=lambda request, tag_name: object_exists_validator(tag_controller.get_tag,
                                                                         _('Tag %(tag_name)s does not exist.') % {'tag_name': tag_name}, tag_name))
def tag_profile(request, tag_name):
    result = ResponseResult()
    tag = request.validation_result.data
    result.data['tag'] = tag

    city = request.user.profile.City if request.user.is_authenticated() else DEFAULT_LOCATION['city']
    pre_city = PredefinedCity.objects.get(City=city)
    user_country = pre_city.Country
    user_city = pre_city.City

    # result.data['shouts2'] = stream_controller.GetStreamShouts(tag.Stream, DEFAULT_PAGE_SIZE * (page_num - 1), DEFAULT_PAGE_SIZE * page_num, False, user_country, user_city)
    # result.data['shouts_count2'] = len(result.data['shouts2'])

    result.data['shouts_count'] = stream_controller.get_stream_shouts_count(tag.Stream)
    result.data['shouts'] = stream_controller.get_stream_shouts(tag.Stream)

    result.data['listeners_count'] = stream_controller.get_stream_listeners(tag.stream2, count_only=True)
    if request.user.is_authenticated():
        result.data['is_listening'] = user_controller.is_listening(request.user, tag.stream2)

    return result


@cached_view(level=CACHE_LEVEL_SESSION,
             tags=[CACHE_TAG_TAGS, CACHE_TAG_STREAMS],
             methods=['GET'],
             api_renderer=tag_api,
             validator=lambda request, tag_name: object_exists_validator(tag_controller.get_tag,
                                                                         _('Tag %(tag_name)s does not exist.') % {'tag_name': tag_name}, tag_name))
def tag_profile_brief(request, tag_name):
    tag = tag_controller.get_tag(tag_name)
    if not tag.Image:
        tag.Image = '/static/img/shout_tag.png'
    result = ResponseResult()
    result.data['tag'] = tag

    result.data['shouts_count'] = Trade.objects.GetValidTrades().filter(Tags=tag).count()
    result.data['listeners_count'] = stream_controller.get_stream_listeners(tag.stream2, count_only=True)
    if request.user.is_authenticated():
        result.data['is_listening'] = user_controller.is_listening(request.user, tag.stream2)
    return result


@cached_view(level=CACHE_LEVEL_SESSION,
             tags=[CACHE_TAG_TAGS, CACHE_TAG_STREAMS],
             json_renderer=json_data_renderer,
             api_renderer=stats_api,
             validator=lambda request, tag_name:
             object_exists_validator(tag_controller.get_tag, _('Tag %(tag_name)s does not exist.') % {'tag_name': tag_name}, tag_name))
def tag_stats(request, tag_name):
    result = ResponseResult()
    tag = request.validation_result.data
    listeners = stream_controller.get_stream_listeners(tag.stream2)

    if hasattr(request, 'is_api') and request.is_api:
        result.data['listeners'] = listeners
    else:
        result.data['listeners'] = [
            {'username': listener.username, 'name': listener.name, 'image': thumbnail(listener.profile.Image, 32)}
            for listener in listeners]
    return result