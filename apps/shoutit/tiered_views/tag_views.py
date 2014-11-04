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


@non_cached_view(methods=['GET', 'POST'],
                 login_required=True,
                 api_renderer=operation_api,
                 json_renderer=lambda request, result, tag_name: json_renderer(request,
                                                                               result,
                                                                               _('You are now listening to shouts about %(tag_name)s.') % {'tag_name': tag_name}),
                 validator=lambda request, tag_name: object_exists_validator(tag_controller.GetTag,
                                                                             _('Tag %(tag_name)s does not exist.') % {'tag_name': tag_name}, tag_name),
                 permissions_required=[PERMISSION_FOLLOW_TAG])
@refresh_cache(tags=[CACHE_TAG_STREAMS, CACHE_TAG_USERS, CACHE_TAG_TAGS])
def add_tag_to_interests(request, tag_name):
    tag_controller.AddToUserInterests(request, tag_name, request.user)
    result = ResponseResult()
    return result


@non_cached_view(methods=['GET', 'DELETE'],
                 login_required=True,
                 api_renderer=operation_api,
                 json_renderer=lambda request, result, tag_name: json_renderer(request,
                                                                               result,
                                                                               _('You are no longer listening to shouts about %(tag_name)s.') % {'tag_name': tag_name},
                                                                               success_message_type='info'),
                 validator=lambda request, tag_name: object_exists_validator(tag_controller.GetTag,
                                                                             _('Tag %(tag_name)s does not exist.') % {'tag_name': tag_name}, tag_name))
@refresh_cache(tags=[CACHE_TAG_STREAMS, CACHE_TAG_USERS, CACHE_TAG_TAGS])
def remove_tag_from_interests(request, tag_name):
    tag_controller.RemoveFromUserInterests(request, tag_name, request.user)
    result = ResponseResult()
    return result


@cached_view(level=CACHE_LEVEL_GLOBAL,
             tags=[CACHE_TAG_TAGS],
             api_renderer=tags_api,
             json_renderer=json_data_renderer,
             methods=['GET'])
def search_tag(request):
    limit = 6
    keyword = request.REQUEST['term']
    tags = list(tag_controller.SearchTags(keyword, limit))
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

    url_encoded_city = None
    if request.GET.has_key('url_encoded_city') and request.GET['url_encoded_city'] != '':
        url_encoded_city = request.GET['url_encoded_city']

    try:
        pre_city = PredefinedCity.objects.get(EncodedCity = url_encoded_city or request.session['user_city_encoded'])
    except ObjectDoesNotExist:
        pre_city = PredefinedCity.objects.get(EncodedCity = 'dubai')

    user_country = pre_city.Country
    user_city = pre_city.City
    profile = user_controller.GetProfile(request.user)
    result.data['top_tags'] = tag_controller.GetTopTags(10, user_country, user_city)
    if request.user.is_authenticated() and isinstance(profile, UserProfile):
        user_interests = profile.Interests.all().values_list('Name')
        for tag in result.data['top_tags']:
            tag['is_interested'] = (tag['Name'], ) in user_interests
    else:
        for tag in result.data['top_tags']:
            tag['is_interested'] = False
    return result


@cached_view(level=CACHE_LEVEL_SESSION,
             tags=[CACHE_TAG_STREAMS, CACHE_TAG_TAGS],
             methods=['GET'],
             api_renderer=shouts_api,
             json_renderer=lambda request, result, username, *args: user_stream_json(request, result),
             validator=lambda request, tag_name, *args, **kwargs: object_exists_validator(tag_controller.GetTag,
                                                                                          _('Tag %(tag_name)s does not exist.') % {'tag_name': tag_name}, tag_name))
def tag_stream(request, tag_name, page_num=None):
    result = ResponseResult()
    if not request.session.has_key('user_country'):
        result.data['shouts_count'] = 0
        result.data['shouts'] = []
        return result

    if not page_num:
        page_num = 1
    else:
        page_num = int(page_num)

    user_country = request.session['user_country']
    user_city = request.session['user_city']

    tag = tag_controller.GetTag(tag_name)

    result.data['shouts_count'] = Trade.objects.GetValidTrades().filter(Tags=tag).count()

    result.data['pages_count'] = int(math.ceil(result.data['shouts_count'] / float(DEFAULT_PAGE_SIZE)))
    result.data['shouts'] = stream_controller.GetStreamShouts(tag.Stream, DEFAULT_PAGE_SIZE * (page_num - 1),
                                                              DEFAULT_PAGE_SIZE * page_num, False, user_country, user_city)
    result.data['is_last_page'] = page_num >= result.data['pages_count']
    result.data['browse_in'] = user_city
    return result


@cached_view(level=CACHE_LEVEL_SESSION,
             tags=[CACHE_TAG_TAGS, CACHE_TAG_STREAMS],
             api_renderer=tag_api,
             html_renderer=lambda request, result, tag_name: object_page_html(request, result, 'tag_profile.html', tag_name),
             methods=['GET'],
             validator=lambda request, tag_name: object_exists_validator(tag_controller.GetTag,
                                                                         _('Tag %(tag_name)s does not exist.') % {'tag_name': tag_name}, tag_name))
def tag_profile(request, tag_name):
    tag = tag_controller.GetTag(tag_name)
    if not tag.Image:
        tag.Image = '/static/img/shout_tag.png'
    result = ResponseResult()
    result.data['tagProfile'] = tag

    page_num = 1

    user_country = request.session['user_country']
    user_city = request.session['user_city']

    result.data['shouts'] = stream_controller.GetStreamShouts(tag.Stream, DEFAULT_PAGE_SIZE * (page_num - 1),
                                                              DEFAULT_PAGE_SIZE * page_num, False, user_country, user_city)
    result.data['children'] = list(tag.ChildTags.all())

    result.data['shouts_count'] = len(result.data['shouts'])
    result.data['followers_count'] = tag.Followers.count()
    if request.user.is_authenticated() and hasattr(request.user, 'Profile'):
        result.data['interested'] = (tag.Name,) in request.user.Profile.Interests.all().values_list('Name')
    result.data['creator_username'] = 'Shoutit'
    result.data['creator'] = None
    return result


@cached_view(level=CACHE_LEVEL_SESSION,
             tags=[CACHE_TAG_TAGS, CACHE_TAG_STREAMS],
             methods=['GET'],
             api_renderer=tag_api,
             validator=lambda request, tag_name: object_exists_validator(tag_controller.GetTag,
                                                                         _('Tag %(tag_name)s does not exist.') % {'tag_name': tag_name}, tag_name))
def tag_profile_brief(request, tag_name):
    tag = tag_controller.GetTag(tag_name)
    if not tag.Image:
        tag.Image = '/static/img/shout_tag.png'
    result = ResponseResult()
    result.data['tagProfile'] = tag

    result.data['shouts_count'] = Trade.objects.GetValidTrades().filter(Tags=tag).count()
    result.data['followers_count'] = tag.Followers.count()
    if request.user.is_authenticated():
        result.data['interested'] = tag in request.user.Profile.Interests.all()
    result.data['creator'] = None
    return result


@cached_view(level=CACHE_LEVEL_SESSION,
             tags=[CACHE_TAG_TAGS, CACHE_TAG_STREAMS],
             json_renderer=json_data_renderer,
             api_renderer=stats_api,
             validator=lambda request, tagName, statsType: object_exists_validator(tag_controller.GetTag,
                                                                                   _('Tag %(tag_name)s does not exist.') % {'tag_name': tagName}, tagName))
def tag_stats(request, tagName, statsType):
    result = ResponseResult()
    if statsType == 'followers':
        followers = tag_controller.TagFollowers(tagName)
        if hasattr(request, 'is_api') and request.is_api:
            result.data['followers'] = followers
        else:
            from apps.shoutit.templatetags import template_filters

            result.data['followers'] = [
                {'username': user.username, 'name': user.name(), 'image': template_filters.thumbnail(user.Image, 32)}
                for user in followers]
    return result