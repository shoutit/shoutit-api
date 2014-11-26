from django.utils.translation import ugettext_lazy as _
from django.views.decorators.csrf import csrf_exempt
from apps.shoutit.controllers import report_controller, gallery_controller, comment_controller, item_controller
from apps.shoutit.forms import *
from apps.shoutit.models import *
from apps.shoutit.permissions import PERMISSION_REPORT
from apps.shoutit.tiered_views.renderers import *
from apps.shoutit.tiered_views.validators import *
from apps.shoutit.tiers import *
from apps.shoutit.constants import *


@csrf_exempt
@non_cached_view(methods=['POST'],
                 login_required=True,
                 json_renderer=lambda request, result, *args: json_renderer(request, result,
                                                                            success_message='Your report was sent successfully'),
                 permissions_required=[PERMISSION_REPORT]
)
def report(request, type, object_pk):
    result = ResponseResult()
    form = ReportForm(request.POST)
    form.is_valid()
    text = form.cleaned_data['text']
    type = int(type)

    attached_object = None
    if type == REPORT_TYPE_USER or type == REPORT_TYPE_BUSINESS:
        attached_object = user_controller.get_profile(object_pk)
    else:
        object_pk = object_pk
        if type == REPORT_TYPE_TRADE or type == REPORT_TYPE_EXPERIENCE:
            attached_object = shout_controller.GetPost(object_pk)
        elif type == REPORT_TYPE_ITEM:
            attached_object = item_controller.get_item(object_pk)
        elif type == REPORT_TYPE_COMMENT:
            attached_object = comment_controller.GetCommentByID(object_pk)

    report_controller.CreateReport(request.user, text, attached_object)
    return result