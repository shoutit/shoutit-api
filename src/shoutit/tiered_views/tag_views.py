from django.utils.translation import ugettext_lazy as _

from shoutit.controllers import stream_controller, user_controller
from shoutit.permissions import PERMISSION_FOLLOW_TAG
from shoutit.tiered_views.renderers import *
from shoutit.tiered_views.validators import *
from shoutit.tiers import *


@non_cached_view(methods=['GET', 'POST'], login_required=True, permissions_required=[PERMISSION_FOLLOW_TAG],
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


@non_cached_view(methods=['GET'], json_renderer=json_data_renderer)
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
        if request.user.is_authenticated() and isinstance(request.user.abstract_profile, Profile):
            profile = request.user.abstract_profile
            user_interests = profile.Interests.all().values_list('name')
            for tag in result.data['tags']:
                tag['is_listening'] = (tag['name'], ) in user_interests
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


@non_cached_view(methods=['GET'], json_renderer=json_data_renderer)
def top_tags(request):
    result = ResponseResult()

    city = request.GET.get('city', '')
    # todo: use country only filter too

    try:
        pre_city = PredefinedCity.objects.get(city=city)
        user_country = pre_city.country
        user_city = pre_city.city
    except PredefinedCity.DoesNotExist:
        user_country = None
        user_city = None

    result.data['tags'] = tag_controller.get_top_tags(10, user_country, user_city)
    if request.user.is_authenticated() and isinstance(request.user.abstract_profile, Profile):
        profile = request.user.abstract_profile
        user_interests = profile.Interests.all().values_list('name')
        for tag in result.data['tags']:
            tag['is_listening'] = (tag['name'], ) in user_interests
    else:
        for tag in result.data['tags']:
            tag['is_listening'] = False
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

    result.data['shouts_count'] = Shout.objects.get_valid_shouts().filter(tags=tag).count()
    result.data['listeners_count'] = stream_controller.get_stream_listeners(tag.stream2, count_only=True)
    if request.user.is_authenticated():
        result.data['is_listening'] = user_controller.is_listening(request.user, tag.stream2)
    return result


@non_cached_view(json_renderer=json_data_renderer,
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
            {'username': listener.username, 'name': listener.name, 'image': listener.profile.image}
            for listener in listeners]
    return result