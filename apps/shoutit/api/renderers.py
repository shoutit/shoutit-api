from apps.shoutit.constants import *
from apps.shoutit.utils import *
from apps.shoutit.api.api_utils import *


def render_shout(shout):
    images = [image.Image for image in shout.GetImages()]
    videos = [render_video(video) for video in shout.get_videos()]
    tags = [render_tag(tag) for tag in shout.GetTags()]
    return {
        'id': IntToBase62(shout.id),
        'url': get_object_url(shout),
        'user': render_user(shout.OwnerUser, True),
        'type': PostType.values[shout.Type],
        'name': None if shout.Type == POST_TYPE_EXPERIENCE else shout.Item.Name,
        'description': shout.Text,
        'price': None if shout.Type == POST_TYPE_EXPERIENCE else shout.Item.Price,
        'currency': None if shout.Type == POST_TYPE_EXPERIENCE else shout.Item.Currency.Code,
        'date_created': shout.DatePublished.strftime('%d/%m/%Y %H:%M:%S%z'),
        'thumbnail':  videos[0]['thumbnail_url'] if videos else shout.GetFirstImage().Image if images else '',
        'images': images,
        'videos': videos,
        'tags': tags,
        'location': {
            'country': shout.CountryCode,
            'city': shout.ProvinceCode,
            'latitude': shout.Latitude,
            'longitude': shout.Longitude,
            'address': shout.Address
        }
    }


def render_tag(tag):
    if tag is None:
        return {}
    if isinstance(tag, unicode):
        tag = Tag(Name=tag)
    #TODO: find what is the case when tag is a dict not instance of Tag class
    elif isinstance(tag, dict):
        tag = Tag(Name=tag['Name'])
    return {
        'name': tag.Name,
        'url': get_object_url(tag),
        'image': tag.Image
    }


def render_user(user, with_phone=False):
    if user is None:
        return {}

    elif isinstance(user, unicode):
        user = apps.shoutit.controllers.user_controller.GetUser(user)
    elif isinstance(user, User):
        try:
            user = user.Profile
        except :
            user = user.Business

    result = {}
    if isinstance(user, UserProfile):
        user, p = user.User, user
        user.Profile = p
        result = {
            'url': get_object_url(user),
            'username': user.username,
            'image': user.Profile.Image,
            #		'image' : get_custom_url(JSON_URL_USER_IMAGE_THUMBNAIL, user.username),
            'name': user.name(),
            'sex': user.Profile.Sex,
            'bio': user.Profile.Bio,
            'is_active': user.is_active
        }
        if with_phone and user.Profile.Mobile:
            result['mobile'] = user.Profile.Mobile
    elif isinstance(user, BusinessProfile):
        result = {
            'url': get_object_url(user.User),
            'username': user.username,
            'image': user.Image,
            #		'image' : get_custom_url(JSON_URL_USER_IMAGE_THUMBNAIL, user.username),
            'name': user.name(),
            'bio': user.About
        }
    return result


def render_message(message):
    if message is None:
        return {}
    return {
        'message_id': IntToBase62(message.id),
        'conversation_id': IntToBase62(message.Conversation.id) ,
        'shout_id': IntToBase62(message.Conversation.AboutPost.id),
        'conversation': get_object_url(message.Conversation),
        'from_user': render_user(message.FromUser),
        'to_user': render_user(message.ToUser),
        'text': message.Text,
        'is_read': message.IsRead,
        'date_created': message.DateCreated.strftime('%d/%m/%Y %H:%M:%S%z')
    }


def render_conversation(conversation):
    if conversation is None:
        return {}
    return {
        'conversation_id': IntToBase62(conversation.id),
        'url': get_object_url(conversation),
        'from_user': render_user(conversation.FromUser),
        'to_user': render_user(conversation.ToUser),
        'about': render_shout(conversation.AboutPost),
        'is_read': conversation.IsRead,
        'text': conversation.Text if hasattr(conversation, 'Text') else '',
        'date_created': conversation.DateCreated.strftime('%d/%m/%Y %H:%M:%S%z') if hasattr(conversation, 'DateCreated') else ''
    }


def render_conversation_full(conversation):
    if conversation is None:
        return {}
    return {
        'url': get_object_url(conversation),
        'from_user': render_user(conversation.FromUser),
        'to_user': render_user(conversation.ToUser),
        'about': render_shout(conversation.AboutPost),
        'is_read': conversation.IsRead,
        'text': conversation.Text if hasattr(conversation, 'Text') else '',
        'conversation_messages': [render_message(message) for message in conversation.messages],
        'date_created': conversation.DateCreated.strftime('%d/%m/%Y %H:%M:%S%z') if hasattr(conversation, 'DateCreated') else ''
    }


def render_experience(experience):
    if experience is None:
        return {}
    else:
        rendered_experience = {
            'id': IntToBase62(experience.id),
            'url': get_object_url(experience),
            'user': render_user(experience.OwnerUser),
            'business': render_user(experience.AboutBusiness),
            'state': experience.State,
            'text': experience.Text,
            'date_created': experience.DatePublished.strftime('%d/%m/%Y %H:%M:%S%z'),
            'detailed': experience.detailed if hasattr(experience,'detailed') else False
        }

        if hasattr(experience,'detailed') and experience.detailed:
            rendered_experience.update({
                'details': {
                    'users_shared_exps': [render_user(user) for user in experience.usersSharedExperience],
                    'comments': [render_comment(comment) for comment in experience.comments],
                    'shared_exps_count': experience.sharedExpsCount,
                    'comments_count': experience.commentsCount,
                    'can_share_exp': experience.canShare,
                    'can_edit_exp': experience.canEdit,
                    'is_owner': experience.isOwner
                }
            })
        return rendered_experience


def render_shared_exp(shared):
    if shared is None:
        return {}
    return {
        'url': get_object_url(shared.Experience),
        'user': render_user(shared.OwnerUser),
        'experience': render_experience(shared.Experience),
        'date_created': shared.DateCreated.strftime('%d/%m/%Y %H:%M:%S%z')
    }


def render_comment(comment):
    if comment is None:
        return {}
    return {
        'url': get_object_url(comment.AboutPost.experience),
        'user': render_user(comment.OwnerUser),
        'post': render_experience(comment.AboutPost.experience),
        'text': comment.Text,
        'date_created': comment.DateCreated.strftime('%d/%m/%Y %H:%M:%S%z')
    }


def render_item(item):
    if item is None:
        return {}
    return {
        'name': item.Name,
        'price': item.Price,
        'currency': item.Currency.Code,
        'date_created': item.DateCreated.strftime('%d/%m/%Y %H:%M:%S%z')
    }


def render_video(video):
    if video is None:
        return {}
    return {
        'url': video.url,
        'thumbnail_url': video.thumbnail_url,
        'provider': video.provider,
        'id_on_provider': video.id_on_provider,
        'duration': video.duration
    }


def render_gallery(gallery):
    if gallery is None:
        return {}
    return {
        #		'url' : get_object_url(gallery),
        #		'business' : render_business(gallery.OwnerBusiness),
    }


def render_gallery_item(gallery_item):
    if gallery_item is None:
        return {}
    return {
        'url': '/gallery_items/%s/' %gallery_item.Gallery.OwnerBusiness.User.username,
        'item': render_item(gallery_item.Item),
        'gallery': render_gallery(gallery_item.Gallery),
        'date_created': gallery_item.DateCreated.strftime('%d/%m/%Y %H:%M:%S%z')
    }


def render_notification(notification):
    if notification is None:
        return {}
    result = {
        'from_user': render_user(notification.FromUser),
        'is_read': notification.IsRead,
        'type': NotificationType.values[notification.Type],
        'date_created': notification.DateCreated.strftime('%d/%m/%Y %H:%M:%S%z'),
        'mark_as_read_url': get_custom_url(JSON_URL_MARK_NOTIFICATION_AS_READ, IntToBase62(notification.pk)),
        'mark_as_unread_url': get_custom_url(JSON_URL_MARK_NOTIFICATION_AS_UNREAD, IntToBase62(notification.pk)),
        'id': notification.id
    }

    if notification.AttachedObject:
        if notification.Type == NOTIFICATION_TYPE_MESSAGE:
            result['attached_object'] = render_message(notification.AttachedObject)
        elif notification.Type == NOTIFICATION_TYPE_FOLLOWSHIP:
            result['attached_object'] = render_user(notification.AttachedObject)
        elif notification.Type == NOTIFICATION_TYPE_EXP_POSTED:
            result['attached_object'] = render_experience(notification.AttachedObject)
        elif notification.Type == NOTIFICATION_TYPE_EXP_SHARED:
            result['attached_object'] = render_shared_exp(notification.AttachedObject)
        elif notification.Type == NOTIFICATION_TYPE_COMMENT:
            result['attached_object'] = render_comment(notification.AttachedObject)
    return result


def render_event(event):
    if event is None:
        return {}
    result = {
        'user' : render_user(event.OwnerUser),
        'event_type' : EventType.values[event.EventType],
        'date_created' : event.DatePublished.strftime('%d/%m/%Y %H:%M:%S%z')
    }

    if event.AttachedObject:
        if event.EventType == EVENT_TYPE_FOLLOW_USER:
            result['attached_object'] = render_user(event.AttachedObject)
        elif event.EventType == EVENT_TYPE_FOLLOW_TAG:
            result['attached_object'] = render_tag(event.AttachedObject)
        elif event.EventType == EVENT_TYPE_SHOUT_OFFER or event.EventType == EVENT_TYPE_SHOUT_REQUEST:
            result['attached_object'] = render_shout(event.AttachedObject)
        elif event.EventType == EVENT_TYPE_EXPERIENCE:
            result['attached_object'] = render_experience(event.AttachedObject)
        elif event.EventType == EVENT_TYPE_SHARE_EXPERIENCE:
            result['attached_object'] = render_shared_exp(event.AttachedObject)
        elif event.EventType == EVENT_TYPE_COMMENT:
            result['attached_object'] = render_comment(event.AttachedObject)
        #		elif event.EventType == EVENT_TYPE_GALLERY_ITEM :
        #			result['attached_object'] = render_gallery_item(event.AttachedObject)
        #		elif event.EventType == EVENT_TYPE_POST_DEAL or event.EventType == EVENT_TYPE_BUY_DEAL :
        #			result['attached_object'] = render_deal(event.AttachedObject)
        return result


def render_currency(currency):
    return {
        'code': currency.Code,
        'name': currency.Name,
        'country': currency.Country
    }


def render_post(post):
    if post.Type == POST_TYPE_BUY or post.Type == POST_TYPE_SELL:
        return render_shout(post)
    #	elif post.Type == POST_TYPE_DEAL:
    #		return render_deal(post)
    elif post.Type == POST_TYPE_EVENT:
        return render_event(post)
    elif post.Type == POST_TYPE_EXPERIENCE:
        return render_experience(post)
    else:
        return {}


import apps.shoutit.controllers.user_controller