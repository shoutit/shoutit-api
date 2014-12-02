from django.views.decorators.csrf import csrf_exempt
from apps.shoutit.constants import REPORT_TYPE_BUSINESS, REPORT_TYPE_USER, REPORT_TYPE_TRADE, REPORT_TYPE_EXPERIENCE, REPORT_TYPE_ITEM, \
    REPORT_TYPE_COMMENT
from apps.shoutit.controllers.comment_controller import GetCommentByID
from apps.shoutit.controllers.item_controller import get_item
from apps.shoutit.controllers.report_controller import CreateReport
from apps.shoutit.controllers.shout_controller import GetPost
from apps.shoutit.controllers.user_controller import get_profile
from apps.shoutit.forms import ReportForm
from apps.shoutit.permissions import PERMISSION_REPORT
from apps.shoutit.tiered_views.renderers import json_renderer
from apps.shoutit.tiers import non_cached_view, ResponseResult


@csrf_exempt
@non_cached_view(methods=['POST'],
                 login_required=True,
                 json_renderer=lambda request, result, *args: json_renderer(request, result,
                                                                            success_message='Your report was sent successfully'),
                 permissions_required=[PERMISSION_REPORT]
)
def report(request, type, object_id):
    result = ResponseResult()
    form = ReportForm(request.POST)
    form.is_valid()
    text = form.cleaned_data['text']
    type = int(type)

    attached_object = None
    if type == REPORT_TYPE_USER or type == REPORT_TYPE_BUSINESS:
        attached_object = get_profile(object_id)
    else:
        object_id = object_id
        if type == REPORT_TYPE_TRADE or type == REPORT_TYPE_EXPERIENCE:
            attached_object = GetPost(object_id)
        elif type == REPORT_TYPE_ITEM:
            attached_object = get_item(object_id)
        elif type == REPORT_TYPE_COMMENT:
            attached_object = GetCommentByID(object_id)

    CreateReport(request.user, text, attached_object)
    return result