
import math
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.csrf import csrf_exempt
import time
from apps.shoutit.controllers import experience_controller,user_controller,business_controller
from apps.shoutit.forms import *
from apps.shoutit.models import *
from apps.shoutit.permissions import PERMISSION_SHOUT_MORE, PERMISSION_SHOUT_REQUEST, PERMISSION_SHOUT_OFFER, PERMISSION_POST_EXPERIENCE, PERMISSION_SHARE_EXPERIENCE, PERMISSION_COMMENT_ON_POST
from apps.shoutit.tiered_views.renderers import *
from apps.shoutit.tiered_views.validators import *
from apps.shoutit.tiers import *
from apps.shoutit.constants import *


@cached_view(methods=['GET'],
	tags=[CACHE_TAG_EXPERIENCES,CACHE_TAG_COMMENTS],
	api_renderer= view_experience_api,
	html_renderer=lambda request, result, *args: page_html(request, result, 'experience.html', result.data['page_title'] if result.data['page_title'] else '', result.data['page_desc'] if result.data['page_desc'] else ''))
def view_experience(request,exp_id):
	result = ResponseResult()
	result.data['timestamp'] = time.mktime(datetime.now().timetuple())
	experience = experience_controller.GetExperience(request.user, Base62ToInt(exp_id),detailed=True)
	result.data['experience'] = experience
	if experience:
		result.data['recent_experiences'] = experience_controller.GetExperiences(user=request.user, about_business=result.data['experience'].AboutBusiness,start_index=0,end_index=5)
		thumps_count = experience_controller.GetBusinessThumbsCount(result.data['experience'].AboutBusiness)
		result.data['thumb_up_count'] = thumps_count['ups']
		result.data['thumb_down_count'] = thumps_count['downs']
		result.data['page_title'] = '%s Experience with %s' % ('Bad' if experience.State == 0 else 'Good', experience.AboutBusiness.name())
		result.data['page_desc'] = experience.Text
		result.data['is_fb_og'] = True
	result.data['report_form'] = ReportForm()
	result.data['comment_form'] = CommentForm()
	return result


#@cached_view(methods=['GET'],
#	tags=[CACHE_TAG_EXPERIENCES,CACHE_TAG_COMMENTS],
#	json_renderer=lambda request, result, *args: experiences_json(request, result),
#	html_renderer=lambda request, result, *args: page_html(request, result, 'experiences.html', _('Experiences')))
#def experiences(request,business_name):
#	result = ResponseResult()
#	result.data['timestamp'] = time.mktime(datetime.now().timetuple())
#	result.data['business_name'] = business_name
#	result.data['experiences'] = experience_controller.GetExperiences(request.user, business_name, start_index=0, end_index= DEFAULT_PAGE_SIZE)
#	result.data['experience_form'] = ExperienceForm()
#	result.data['comment_form'] = CommentForm()
#	return result


@cached_view(methods=['GET'],
	tags=[CACHE_TAG_EXPERIENCES,CACHE_TAG_COMMENTS],
	api_renderer=experiences_api,
	json_renderer=lambda request, result, *args: experiences_stream_json(request, result))
def experiences_stream(request,username, page_num=None):
	if username == '@me':
		username = request.user.username

	if not page_num:
		page_num = 1
	else:
		page_num = int(page_num)
	result = ResponseResult()
	profile = user_controller.GetUser(username)
	experiences_count = experience_controller.GetExperiencesCount(profile)

	result.data['pages_count'] = int(math.ceil(experiences_count / float(DEFAULT_PAGE_SIZE)))

	if profile and isinstance(profile, UserProfile):
		result.data['experiences'] = experience_controller.GetExperiences(user=request.user, owner_user=profile.User, start_index = DEFAULT_PAGE_SIZE * (page_num - 1), end_index = DEFAULT_PAGE_SIZE * page_num)
	elif profile and isinstance(profile, BusinessProfile):
		result.data['experiences'] = experience_controller.GetExperiences(user=request.user, about_business=profile, start_index = DEFAULT_PAGE_SIZE * (page_num - 1), end_index = DEFAULT_PAGE_SIZE * page_num)

	result.data['comment_form'] = CommentForm()
	result.data['timestamp'] = time.mktime(datetime.now().timetuple())
	result.data['is_last_page'] = page_num >= result.data['pages_count']
	return result

def get_business_initials(username):
	if not (username and len(username) > 0):
		return {}
	business = business_controller.GetBusiness(username)
	cat = business.Category and business.Category.pk or 0
	init = {'name': business.Name, 'category': cat, 'location': str(business.Latitude) + ', ' + str(business.Longitude),
			'country': business.Country, 'city': business.City, 'address': business.Address, 'username': username}
	return init

@csrf_exempt
@non_cached_view(
	methods=['POST'],
	login_required=True,
	json_renderer = lambda request, result, username : post_experience_json_renderer(request,result),
	api_renderer= view_experience_api,
	validator=lambda request, *args, **kwargs : experience_validator(request, initial = get_business_initials(args and args[0] or (kwargs.has_key('username') and kwargs['username'] or '')), *args, **kwargs),
#	form_validator(request,ExperienceForm),
	permissions_required=[PERMISSION_POST_EXPERIENCE]
)
@refresh_cache(tags=[CACHE_TAG_EXPERIENCES,CACHE_TAG_USERS])
def post_exp(request, username = None):
	result = ResponseResult()
	form = ExperienceForm(request.POST)
	form.is_valid()
	username = username or form.cleaned_data['username']
	if username is None or username == '':
		business_form = CreateTinyBusinessForm(request.POST)
		business_form.is_valid()
		latlng = business_form.cleaned_data.has_key('location') and business_form.cleaned_data['location'] or ''
		lat = len(latlng) and latlng.split(',')[0].strip() or 0.0
		lng = len(latlng) and latlng.split(',')[1].strip() or 0.0
		business = business_controller.CreateTinyBusinessProfile(
			business_form.cleaned_data['name'],
			business_form.cleaned_data.has_key('category') and business_form.cleaned_data['category'] or None,
			lat, lng,
			business_form.cleaned_data.has_key('country') and business_form.cleaned_data['country'] or None,
			business_form.cleaned_data.has_key('city') and business_form.cleaned_data['city'] or None,
			business_form.cleaned_data.has_key('address') and business_form.cleaned_data['address'] or None,
			business_form.cleaned_data.has_key('source') and business_form.cleaned_data['source'] or None,
			business_form.cleaned_data.has_key('source_id') and business_form.cleaned_data['source_id'] or None)
	else:
		business = business_controller.GetBusiness(username)

	result.data['experience'] = experience_controller.PostExperience(request.user, int(EXPERIENCE_UP) if int(form.cleaned_data['state']) else int(EXPERIENCE_DOWN), form.cleaned_data['text'],business)
	result.messages.append(('success', _('Your experience was posted successfully')))
	return result


@csrf_exempt
@non_cached_view(methods=['POST'],
	login_required=True,
	api_renderer = operation_api,
	json_renderer = lambda request, result, exp_id: json_renderer(request,result,success_message = _('You have shared the experience successfully.')),
	validator=lambda request, exp_id: share_experience_validator(request,exp_id),
	permissions_required=[PERMISSION_SHARE_EXPERIENCE]
	)
@refresh_cache(tags=[CACHE_TAG_EXPERIENCES])
def share_experience(request, exp_id):
	shared = experience_controller.ShareExperience(request.user, Base62ToInt(exp_id))
	result = ResponseResult()
	return result


@csrf_exempt
@non_cached_view(methods=['POST'],
	json_renderer = lambda request, result, exp_id: post_experience_json_renderer(request,result,message = _('Your experience was edit successfully.')),
	validator=lambda request, exp_id: edit_experience_validator(request,exp_id),
	)
@refresh_cache(tags=[CACHE_TAG_EXPERIENCES])
def edit_experience(request, exp_id):
	result = ResponseResult()
	form = ExperienceForm(request.POST)
	form.is_valid()
	result.data['experience'] = experience_controller.EditExperience(Base62ToInt(exp_id),EXPERIENCE_UP if int(form.cleaned_data['state']) else EXPERIENCE_DOWN,form.cleaned_data['text'])
	return result


@non_cached_view(methods=['GET'],
	json_renderer = lambda request, result, exp_id: user_json_renderer(request,result),
	validator=lambda request, exp_id: object_exists_validator(shout_controller.GetPost,_('Experience dose not exist.'), Base62ToInt(exp_id)),
	)
def users_shared_experience(request, exp_id):
	result = ResponseResult()
	result.data['users'] = experience_controller.GetUsersSharedExperience(Base62ToInt(exp_id))
	return result