from django.core.exceptions import ObjectDoesNotExist
from apps.shoutit.constants import *


def CommentOnPost(user, post_id, text):
	post = shout_controller.GetPost(post_id)
	if post:
		comment = Comment(AboutPost = post,OwnerUser = user,Text = text)
		comment.save()
		event_controller.RegisterEvent(user, EVENT_TYPE_COMMENT, comment)

		seen = set()
		seen_add = seen.add
		users = [comment.OwnerUser for comment in GetPostComments(post_id) if comment.OwnerUser not in seen and not seen_add(comment.OwnerUser)]
		if post.OwnerUser not in seen and not seen_add(post.OwnerUser):
			users.append(post.OwnerUser)
		users.remove(user)
		notifications_controller.NotifyUsersOfComment(users,comment)
		realtime_controller.BindUserToPost(user,post)
		return comment
	else:
		raise ObjectDoesNotExist()

def GetPostComments(post_id, date = None, start_index = None, end_index = None):
#	post = shout_controller.GetPost(post_id)
#	if post:
	comments = Comment.objects.filter(AboutPost__pk = post_id,IsDisabled = False).select_related('OwnerUser','OwnerUser__Profile','OwnerUser__Business').order_by('DateCreated')
	if date:
		comments = comments.filter(DateCreated__lte = date)
	if start_index:
		if end_index: 
			comments = list(comments)[start_index:end_index]
		else:
			comments = list(comments)[start_index:]
	return comments

def GetCommentByID(comment_id):
	comment = Comment.objects.get(pk = comment_id)
	if comment:
		return comment
	else :
		return None


def DeleteComment(comment_id):
	comment = Comment.objects.get(pk = comment_id)
	if comment:
		comment.IsDisabled = True
		comment.save()
		event_controller.DeleteEventAboutObj(comment)

from apps.shoutit import constants, utils
from apps.shoutit.controllers import event_controller,shout_controller,notifications_controller,realtime_controller
from apps.shoutit.models import Comment