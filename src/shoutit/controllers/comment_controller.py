from django.core.exceptions import ObjectDoesNotExist

from common.constants import *


def CommentOnPost(user, post_id, text):
    post = shout_controller.get_post(post_id)
    if post:
        comment = Comment(AboutPost=post, user=user, text=text)
        comment.save()
        event_controller.register_event(user, EVENT_TYPE_COMMENT, comment)

        seen = set()
        seen_add = seen.add
        users = [comment.user for comment in GetPostComments(post_id) if comment.user not in seen and not seen_add(comment.user)]
        if post.user not in seen and not seen_add(post.user):
            users.append(post.user)
        users.remove(user)
        notifications_controller.notify_users_of_comment(users, comment)
        realtime_controller.BindUserToPost(user, post)
        return comment
    else:
        raise ObjectDoesNotExist()


def GetPostComments(post_id, date=None, start_index=None, end_index=None):
    # post = shout_controller.get_post(post_id)
    #	if post:
    comments = Comment.objects.filter(AboutPost__pk=post_id, is_disabled=False).select_related('user', 'user__Profile',
                                                                                              'user__Business').order_by('DateCreated')
    if date:
        comments = comments.filter(DateCreated__lte=date)
    if start_index:
        if end_index:
            comments = list(comments)[start_index:end_index]
        else:
            comments = list(comments)[start_index:]
    return comments


def GetCommentByID(comment_id):
    comment = Comment.objects.get(pk=comment_id)
    if comment:
        return comment
    else:
        return None


def DeleteComment(comment_id):
    comment = Comment.objects.get(pk=comment_id)
    if comment:
        comment.is_disabled = True
        comment.save()
        event_controller.delete_event_about_obj(comment)


from shoutit.controllers import event_controller, shout_controller, notifications_controller, realtime_controller
from shoutit.models import Comment