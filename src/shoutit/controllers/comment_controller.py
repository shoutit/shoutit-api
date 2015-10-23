from __future__ import unicode_literals
from django.core.exceptions import ObjectDoesNotExist

from common.constants import *  # NOQA


def CommentOnPost(user, post_id, text):
    post = shout_controller.get_post(post_id)
    if post:
        comment = Comment(AboutPost=post, user=user, text=text)
        comment.save()

        seen = set()
        seen_add = seen.add
        users = [_comment.user for _comment in GetPostComments(post_id) if
                 _comment.user not in seen and not seen_add(_comment.user)]
        if post.user not in seen and not seen_add(post.user):
            users.append(post.user)
        users.remove(user)
        notifications_controller.notify_users_of_comment(users, comment)
        return comment
    else:
        raise ObjectDoesNotExist()


def GetPostComments(post_id, date=None, start_index=None, end_index=None):
    # post = shout_controller.get_post(post_id)
    # if post:
    comments = Comment.objects.filter(AboutPost__pk=post_id, is_disabled=False).select_related(
        'user', 'user__profile',
        'user__business').order_by('created_at')
    if date:
        comments = comments.filter(created_at__lte=date)
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


from shoutit.controllers import shout_controller, notifications_controller
from shoutit.models import Comment
