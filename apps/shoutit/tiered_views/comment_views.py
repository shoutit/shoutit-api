from datetime import datetime
import time

from django.views.decorators.csrf import csrf_exempt
from django.utils.translation import ugettext_lazy as _

from common.constants import DEFAULT_PAGE_SIZE
from apps.shoutit.forms import CommentForm
from apps.shoutit.controllers.comment_controller import CommentOnPost, GetPostComments, DeleteComment
from apps.shoutit.controllers.shout_controller import GetPost
from apps.shoutit.permissions import PERMISSION_COMMENT_ON_POST
from apps.shoutit.tiered_views.renderers import comment_on_post_json_renderer, operation_api, api_post_comments, json_renderer, \
    post_comments_json_renderer
from apps.shoutit.tiered_views.validators import comment_on_post_validator, object_exists_validator, delete_comment_validator
from apps.shoutit.tiers import non_cached_view, CACHE_TAG_COMMENTS, refresh_cache, ResponseResult


@csrf_exempt
@non_cached_view(methods=['POST'],
                 login_required=True,
                 json_renderer=lambda request, result, post_id: comment_on_post_json_renderer(request, result),
                 validator=lambda request, post_id: comment_on_post_validator(request, post_id, CommentForm),
                 api_renderer=operation_api,
                 permissions_required=[PERMISSION_COMMENT_ON_POST]
)
@refresh_cache(tags=[CACHE_TAG_COMMENTS])
def comment_on_post(request, post_id):
    result = ResponseResult()
    form = CommentForm(request.POST)
    form.is_valid()
    result.data['comment'] = CommentOnPost(request.user, post_id, form.cleaned_data['text'])
    return result


@csrf_exempt
@non_cached_view(methods=['POST'],
                 json_renderer=lambda request, result, *args: json_renderer(request, result),
                 validator=lambda request, comment_id: delete_comment_validator(request, comment_id),
)
@refresh_cache(tags=[CACHE_TAG_COMMENTS])
def delete_comment(request, comment_id):
    result = ResponseResult()
    DeleteComment(comment_id)
    return result


@non_cached_view(methods=['GET'],
                 json_renderer=lambda request, result, post_id: post_comments_json_renderer(request, result),
                 api_renderer=api_post_comments,
                 validator=lambda request, post_id: object_exists_validator(GetPost, _('post dose not exist.'), post_id),
)
def post_comments(request, post_id):
    result = ResponseResult()
    page = int(request.GET.get('page', 0))
    timestamp = float(request.GET.get('timestamp', time.mktime(datetime.now().timetuple()) + 5))

    start_index = -(page + 1) * DEFAULT_PAGE_SIZE
    end_index = -page * DEFAULT_PAGE_SIZE if page != 0 else None
    date = datetime.fromtimestamp(timestamp)
    comments = GetPostComments(post_id, date=date, start_index=start_index, end_index=end_index)
    for comment in comments:
        comment.isOwner = True if comment.OwnerUser == request.user else False
    result.data['comments'] = comments
    result.data['timestamp'] = timestamp
    return result
