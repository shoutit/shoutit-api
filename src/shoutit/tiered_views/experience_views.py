from datetime import datetime
import math
import time

from django.utils.translation import ugettext_lazy as _
from django.views.decorators.csrf import csrf_exempt

from common.constants import DEFAULT_PAGE_SIZE, EXPERIENCE_UP, EXPERIENCE_DOWN
from shoutit.controllers.business_controller import GetBusiness, CreateTinyBusinessProfile
from shoutit.controllers.experience_controller import GetExperience, GetBusinessThumbsCount, GetExperiences, GetExperiencesCount, \
    PostExperience, EditExperience, GetUsersSharedExperience, ShareExperience
from shoutit.controllers.shout_controller import get_post
from shoutit.controllers.user_controller import get_profile
from shoutit.forms import ReportForm, CommentForm, CreateTinyBusinessForm, ExperienceForm
from shoutit.models import Profile, Business
from shoutit.permissions import PERMISSION_POST_EXPERIENCE, PERMISSION_SHARE_EXPERIENCE
from shoutit.tiered_views.renderers import page_html, experiences_stream_json, \
    post_experience_json_renderer, json_renderer, user_json_renderer
from shoutit.tiered_views.validators import experience_validator, share_experience_validator, edit_experience_validator, \
    object_exists_validator, experience_view_validator
from shoutit.tiers import ResponseResult, non_cached_view


@non_cached_view(methods=['GET'], validator=experience_view_validator,
                 html_renderer=lambda request, result, *args: page_html(request, result, 'experience.html',
                                                                        result.data['page_title'] if result.data['page_title'] else '',
                                                                        result.data['page_desc'] if result.data['page_desc'] else ''))
def view_experience(request, exp_id):
    result = ResponseResult()
    result.data['timestamp'] = time.mktime(datetime.now().timetuple())
    experience = GetExperience(exp_id, request.user, detailed=True)
    result.data['experience'] = experience
    if experience:
        result.data['recent_experiences'] = GetExperiences(user=request.user,
                                                           about_business=result.data['experience'].AboutBusiness,
                                                           start_index=0, end_index=5)
        thumps_count = GetBusinessThumbsCount(result.data['experience'].AboutBusiness)
        result.data['thumb_up_count'] = thumps_count['ups']
        result.data['thumb_down_count'] = thumps_count['downs']
        result.data['page_title'] = '%s Experience with %s' % ('Bad' if experience.State == 0 else 'Good', experience.AboutBusiness.name)
        result.data['page_desc'] = experience.text
        result.data['is_fb_og'] = True
    result.data['report_form'] = ReportForm()
    result.data['comment_form'] = CommentForm()
    return result


# @cached_view(methods=['GET'],
# tags=[CACHE_TAG_EXPERIENCES,CACHE_TAG_COMMENTS],
# json_renderer=lambda request, result, *args: experiences_json(request, result),
# html_renderer=lambda request, result, *args: page_html(request, result, 'experiences.html', _('Experiences')))
# def experiences(request,business_name):
# result = ResponseResult()
# result.data['timestamp'] = time.mktime(datetime.now().timetuple())
#	result.data['business_name'] = business_name
#	result.data['experiences'] = experience_controller.GetExperiences(request.user, business_name, start_index=0, end_index= DEFAULT_PAGE_SIZE)
#	result.data['experience_form'] = ExperienceForm()
#	result.data['comment_form'] = CommentForm()
#	return result


@non_cached_view(methods=['GET'], json_renderer=lambda request, result, *args: experiences_stream_json(request, result))
def experiences_stream(request, username, page_num=None):
    if username == 'me':
        username = request.user.username

    if not page_num:
        page_num = 1
    else:
        page_num = int(page_num)
    result = ResponseResult()
    profile = get_profile(username)
    experiences_count = GetExperiencesCount(profile)

    result.data['pages_count'] = int(math.ceil(experiences_count / float(DEFAULT_PAGE_SIZE)))

    if profile and isinstance(profile, Profile):
        result.data['experiences'] = GetExperiences(user=request.user, owner_user=profile.user,
                                                    start_index=DEFAULT_PAGE_SIZE * (page_num - 1),
                                                    end_index=DEFAULT_PAGE_SIZE * page_num)
    elif profile and isinstance(profile, Business):
        result.data['experiences'] = GetExperiences(user=request.user, about_business=profile,
                                                    start_index=DEFAULT_PAGE_SIZE * (page_num - 1),
                                                    end_index=DEFAULT_PAGE_SIZE * page_num)

    result.data['comment_form'] = CommentForm()
    result.data['timestamp'] = time.mktime(datetime.now().timetuple())
    result.data['is_last_page'] = page_num >= result.data['pages_count']
    return result


def get_business_initials(username):
    if not (username and len(username) > 0):
        return {}
    business = GetBusiness(username)
    cat = business.Category and business.Category.pk or 0
    init = {'name': business.name, 'category': cat, 'location': str(business.latitude) + ', ' + str(business.longitude),
            'country': business.country, 'city': business.city, 'address': business.address, 'username': username}
    return init


@csrf_exempt
@non_cached_view(methods=['POST'], login_required=True, permissions_required=[PERMISSION_POST_EXPERIENCE],
                 json_renderer=lambda request, result, username: post_experience_json_renderer(request, result),
                 validator=lambda request, *args, **kwargs: experience_validator(request, initial=get_business_initials(
                     args and args[0] or ('username' in kwargs and kwargs['username'] or '')), *args, **kwargs)
                 # form_validator(request,ExperienceForm),
)
def post_exp(request, username=None):
    result = ResponseResult()
    form = ExperienceForm(request.POST)
    form.is_valid()
    username = username or form.cleaned_data['username']
    if username is None or username == '':
        business_form = CreateTinyBusinessForm(request.POST)
        business_form.is_valid()
        latlng = 'location' in business_form.cleaned_data and business_form.cleaned_data['location'] or ''
        lat = len(latlng) and latlng.split(',')[0].strip() or 0.0
        lng = len(latlng) and latlng.split(',')[1].strip() or 0.0
        business = CreateTinyBusinessProfile(
            business_form.cleaned_data['name'],
            'category' in business_form.cleaned_data and business_form.cleaned_data['category'] or None,
            lat, lng,
            'country' in business_form.cleaned_data and business_form.cleaned_data['country'] or None,
            'city' in business_form.cleaned_data and business_form.cleaned_data['city'] or None,
            'address' in business_form.cleaned_data and business_form.cleaned_data['address'] or None,
            'source' in business_form.cleaned_data and business_form.cleaned_data['source'] or None,
            'source_id' in business_form.cleaned_data and business_form.cleaned_data['source_id'] or None)
    else:
        business = GetBusiness(username)

    result.data['experience'] = PostExperience(request.user, int(EXPERIENCE_UP) if int(form.cleaned_data['state']) else int(
        EXPERIENCE_DOWN), form.cleaned_data['text'], business)
    result.messages.append(('success', _('Your experience was posted successfully')))
    return result


@csrf_exempt
@non_cached_view(methods=['POST'], login_required=True, permissions_required=[PERMISSION_SHARE_EXPERIENCE],
                 validator=lambda request, exp_id: share_experience_validator(request, exp_id),
                 json_renderer=lambda request, result, exp_id: json_renderer(request, result, success_message=_(
                     'You have shared the experience successfully.'))
)
def share_experience(request, exp_id):
    shared = ShareExperience(request.user, exp_id)
    result = ResponseResult()
    return result


@csrf_exempt
@non_cached_view(methods=['POST'],
                 json_renderer=lambda request, result, exp_id: post_experience_json_renderer(request, result, message=_(
                     'Your experience was edit successfully.')),
                 validator=lambda request, exp_id: edit_experience_validator(request, exp_id)
)
def edit_experience(request, exp_id):
    result = ResponseResult()
    form = ExperienceForm(request.POST)
    form.is_valid()
    result.data['experience'] = EditExperience(exp_id, EXPERIENCE_UP if int(form.cleaned_data['state']) else EXPERIENCE_DOWN,
                                               form.cleaned_data['text'])
    return result


@non_cached_view(methods=['GET'],
                 json_renderer=lambda request, result, exp_id: user_json_renderer(request, result),
                 validator=lambda request, exp_id: object_exists_validator(get_post, True, _('Experience dose not exist.'), exp_id),
)
def users_shared_experience(request, exp_id):
    result = ResponseResult()
    result.data['users'] = GetUsersSharedExperience(exp_id)
    return result