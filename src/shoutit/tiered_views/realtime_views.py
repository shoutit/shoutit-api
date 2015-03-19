from shoutit.tiers import non_cached_view, ResponseResult
from shoutit.tiered_views.renderers import json_renderer, notifications_html, notifications_json
from shoutit.controllers import message_controller, notifications_controller, user_controller


# todo: refactor notification views: notifications, notifications_al
@non_cached_view(methods=['GET'], login_required=True, html_renderer=notifications_html, json_renderer=notifications_json)
def notifications(request):
    result = ResponseResult()
    profile = request.user.abstract_profile
    if request.is_ajax() or (hasattr(request, 'is_api') and request.is_api):
        result.data['notifications'] = user_controller.get_notifications(profile)
    else:
        result.data['notifications'] = user_controller.get_all_notifications(profile)

    notifications_controller.mark_all_as_read(request.user)
    return result


@non_cached_view(methods=['GET'], login_required=True,
                 json_renderer=lambda request, result: json_renderer(request, result, success_message='', data=result.data)
)
def notifications_count(request):
    result = ResponseResult()
    result.data['notifications_count'] = user_controller.get_unread_notifications_count(request.user.abstract_profile)
    result.data['notifications_count_wo_messages'] = notifications_controller.get_user_notifications_without_messages_count(request.user)
    result.data['unread_conversations'] = message_controller.UnReadConversationsCount(request.user)
    return result


@non_cached_view(methods=['GET'], json_renderer=notifications_json, login_required=True)
def notifications_all(request):
    result = ResponseResult()
    result.data['notifications'] = user_controller.get_all_notifications(request.user.profile)
    notifications_controller.mark_all_as_read(request.user)
    return result

