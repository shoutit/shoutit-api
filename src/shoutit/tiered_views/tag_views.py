import math

from django.utils.translation import ugettext_lazy as _

from shoutit.controllers import stream_controller, tag_controller, user_controller
from shoutit.permissions import PERMISSION_FOLLOW_TAG
from shoutit.tiered_views.renderers import *
from shoutit.tiered_views.validators import *
from shoutit.tiers import *
from common.constants import *
from shoutit.templatetags.template_filters import thumbnail


@non_cached_view(methods=['GET', 'POST'], login_required=True, permissions_required=[PERMISSION_FOLLOW_TAG],
                 api_renderer=operation_api,
                 json_renderer=lambda request, result, tag_name:
                 json_renderer(request, result, _('You are now listening to shouts about %(tag_name)s.') % {'tag_name': tag_name}),
                 validator=lambda request, tag_name:
                 object_exists_validator(tag_controller.get_tag, False, _('Tag %(tag_name)s does not exist.') % {'tag_name': tag_name},
                                         tag_name))
def start_listening_to_tag(request, tag_name):
    result = ResponseResult()
    tag = request.validation_result.data
    stream_controller.listen_to_stream(request.user, tag.stream2)
    return result


@non_cached_view(methods=['GET', 'DELETE'], login_required=True,
                 api_renderer=operation_api,
                 json_renderer=lambda request, result, tag_name:
                 json_renderer(request, result, _('You are no longer listening to shouts about %(tag_name)s.') % {'tag_name': tag_name},
                               success_message_type='info'),
                 validator=lambda request, tag_name:
                 object_exists_validator(tag_controller.get_tag, False, _('Tag %(tag_name)s does not exist.') % {'tag_name': tag_name},
                                         tag_name))
def stop_listening_to_tag(request, tag_name):
    result = ResponseResult()
    tag = request.validation_result.data
    stream_controller.remove_listener_from_stream(request.user, tag.stream2)
    return result


@non_cached_view(methods=['GET'], api_renderer=tags_api, json_renderer=json_data_renderer)
def search_tag(request):
    result = ResponseResult()

    query = request.GET.get('query', '')
    limit = request.GET.get('limit', 10)
    show_is_listening = bool(request.GET.get('show_is_listening', False))

    if limit > 10:
        limit = 10
    tags = tag_controller.search_tags(query, limit)
    result.data['tags'] = tags

    if show_is_listening:
        profile = user_controller.GetProfile(request.user)
        if request.user.is_authenticated() and isinstance(profile, Profile):
            user_interests = profile.Interests.all().values_list('Name')
            for tag in result.data['tags']:
                tag['is_listening'] = (tag['Name'], ) in user_interests
        else:
            for tag in result.data['tags']:
                tag['is_listening'] = False

    return result


@non_cached_view(methods=['GET'],
                 json_renderer=json_data_renderer)
def set_tag_parent(request):
    result = ResponseResult()
    tag_controller.setTagParent(request.GET[u'child_id'], request.GET[u'parent_name'])
    return result


@non_cached_view(methods=['GET'], api_renderer=tags_api, json_renderer=json_data_renderer)
def top_tags(request):
    result = ResponseResult()

    city = request.GET.get('city', '')
    # todo: use country only filter too

    try:
        pre_city = PredefinedCity.objects.get(City=city)
        user_country = pre_city.Country
        user_city = pre_city.City
    except PredefinedCity.DoesNotExist:
        user_country = None
        user_city = None

    profile = user_controller.GetProfile(request.user)
    result.data['tags'] = tag_controller.get_top_tags(10, user_country, user_city)
    if request.user.is_authenticated() and isinstance(profile, Profile):
        user_interests = profile.Interests.all().values_list('Name')
        for tag in result.data['tags']:
            tag['is_listening'] = (tag['Name'], ) in user_interests
    else:
        for tag in result.data['tags']:
            tag['is_listening'] = False
    return result


@non_cached_view(methods=['GET'], api_renderer=shouts_api,
                 json_renderer=lambda request, result, tag_name, *args: user_stream_json(request, result),
                 validator=lambda request, tag_name, *args, **kwargs: object_exists_validator(tag_controller.get_tag, False,
                                                                                              _('Tag %(tag_name)s does not exist.') % {
                                                                                                  'tag_name': tag_name}, tag_name))
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


@non_cached_view(methods=['GET'], api_renderer=tag_api,
                 html_renderer=lambda request, result, tag_name: object_page_html(request, result, 'tag_profile.html', tag_name),

                 validator=lambda request, tag_name: object_exists_validator(tag_controller.get_tag, False,
                                                                             _('Tag %(tag_name)s does not exist.') % {'tag_name': tag_name},
                                                                             tag_name))
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


@non_cached_view(methods=['GET'],
                 validator=lambda request, tag_name: object_exists_validator(tag_controller.get_tag, False,
                                                                             _('Tag %(tag_name)s does not exist.') % {'tag_name': tag_name},
                                                                             tag_name))
def tag_profile_brief(request, tag_name):
    tag = tag_controller.get_tag(tag_name)
    if not tag.image:
        tag.image = '/static/img/shout_tag.png'
    result = ResponseResult()
    result.data['tag'] = tag

    result.data['shouts_count'] = Trade.objects.get_valid_trades().filter(Tags=tag).count()
    result.data['listeners_count'] = stream_controller.get_stream_listeners(tag.stream2, count_only=True)
    if request.user.is_authenticated():
        result.data['is_listening'] = user_controller.is_listening(request.user, tag.stream2)
    return result


@non_cached_view(json_renderer=json_data_renderer, api_renderer=stats_api,
                 validator=lambda request, tag_name:
                 object_exists_validator(tag_controller.get_tag, False, _('Tag %(tag_name)s does not exist.') % {'tag_name': tag_name},
                                         tag_name))
def tag_stats(request, tag_name):
    result = ResponseResult()
    tag = request.validation_result.data
    listeners = stream_controller.get_stream_listeners(tag.stream2)

    if hasattr(request, 'is_api') and request.is_api:
        result.data['listeners'] = listeners
    else:
        result.data['listeners'] = [
            {'username': listener.username, 'name': listener.name, 'image': thumbnail(listener.profile.image, 32)}
            for listener in listeners]
    return result