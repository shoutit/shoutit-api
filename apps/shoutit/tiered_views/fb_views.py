from django.template import RequestContext
from django.shortcuts import render_to_response
from django.views.decorators.csrf import csrf_exempt
from django.utils.translation import ugettext_lazy as _
from apps.shoutit.tiered_views.renderers import *
from apps.shoutit.tiers import *

from apps.shoutit.models import Profile, LinkedFacebookAccount, Shout, FbContest, User
from apps.shoutit.tiers import ResponseResult
from apps.shoutit.utils import *


@csrf_exempt
def fb_tab(request, template=None):
    signed_request = request.REQUEST['signed_request']

    fb_data = parse_signed_request(signed_request, settings.FACEBOOK_APP_SECRET)

    variables = RequestContext(request, fb_data)
    return render_to_response('fb/fb_tab.html', variables)


def fb_connect(request, template=None):
    return render_to_response('fb/fb_connect.html')


def fb_share(request, template=None):
    return render_to_response('fb/fb_share.html')


@csrf_exempt
def fb_tab_edit(request, template=None):
    variables = RequestContext(request)
    return render_to_response('fb/fb_tab_edit.html', variables)


@csrf_exempt
def fb_comp(request, comp_num, template=None):
    signed_request = request.REQUEST['signed_request']
    fb_data = parse_signed_request(signed_request, '1411c146d781128661db9ecef42ea97c')
    fb_data['page_num'] = 1
    user = request.user
    fb_contest = FbContest.objects.filter(user=user) if user.pk else None
    fb_data['joined'] = True if fb_contest else False
    variables = RequestContext(request, fb_data)
    return render_to_response('fb/comp_1.html', variables)


@csrf_exempt
def fb_comp_page(request, comp_num, template=None):
    page_num = request.GET['page'] if request.GET.has_key('page') else '1'
    variables = {}
    variables['page_num'] = int(page_num)
    if variables['page_num'] == 1:
        user = request.user
        fb_contest = FbContest.objects.filter(user=user) if user.pk else None
        variables['joined'] = True if fb_contest else False

    variables = RequestContext(request, variables)
    return render_to_response('fb/comp_%s.html' % page_num, variables)


@csrf_exempt
def fb_comp_add(request, comp_num=1, user_name=None, fb_id=None, share_id=None, template=None):
    result = ResponseResult()
    user = User.objects.get(username=user_name)
    fb_contest = None
    if user and fb_id and share_id:
        fb_contest = FbContest(ContestId=comp_num, user=user, FbId=fb_id, ShareId=share_id)
        fb_contest.save()
    result.data['fb_contest'] = fb_contest.pk if fb_contest else None
    return json_data_renderer(request, result)
