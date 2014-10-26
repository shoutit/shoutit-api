from apps.shoutit.models import User, UserProfile, BusinessProfile, Tag
from apps.shoutit.constants import *
from apps.shoutit.utils import IntToBase62
from apps.shoutit.api.api_utils import get_custom_url, get_object_url, api_urls
from apps.shoutit.controllers.user_controller import GetUser


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
        'date_created': shout.DatePublished.strftime('%s'),
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


#TODO: rendering levels in better way.
# 1: username and name
# 2: url, image, sex, is_active
# 3: date_joined, bio, location
# 4: ?
# 5: ?
def render_user(user, owner=False, level=1):
    if user is None:
        return {}

    profile = None
    result = {}
    if isinstance(user, unicode):
        profile = GetUser(user)

    elif isinstance(user, User):
        try:
            profile = user.Profile
        except AttributeError:
            profile = user.Business

    if isinstance(profile, UserProfile):

        result = {
            'name': user.name(),
            'username': user.username
        }

        if level == 2:
            result.update({
                'url': get_object_url(user),
                'image': profile.Image,
                'sex': profile.Sex,
                'is_active': user.is_active
            })

        if level >= 3:
            result.update({
                'date_joined': user.date_joined.strftime('%s'),
                'bio': profile.Bio,
                'location': {
                    'country': profile.Country,
                    'city': profile.City

                }
            })
            if owner:
                result['location'].update({
                    'latitude': profile.Latitude,
                    'longitude': profile.Longitude
                })

    elif isinstance(profile, BusinessProfile):
        result = {
            'url': get_object_url(user.User),
            'username': user.username,
            'image': profile.Image,
            'name': user.name(),
            'bio': profile.About,
            'location': {
                'country': profile.Country,
                'city': profile.City,
                'address': profile.Address
            }
            #todo: other business attributes

        }
    return result


def render_message(message):
    if message is None:
        return {}
    return {
        'message_id': IntToBase62(message.id),
        'conversation_id': IntToBase62(message.Conversation.id) ,
        'shout_id': IntToBase62(message.Conversation.AboutPost.id),
        'from_user': render_user(message.FromUser),
        'to_user': render_user(message.ToUser),
        'text': message.Text,
        'is_read': message.IsRead,
        'date_created': message.DateCreated.strftime('%s')
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
        'date_created': hasattr(conversation, 'DateCreated') and conversation.DateCreated.strftime('%s') or None
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
        'date_created': hasattr(conversation, 'DateCreated') and conversation.DateCreated.strftime('%s') or None
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
            'date_created': experience.DatePublished.strftime('%s'),
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
        'date_created': shared.DateCreated.strftime('%s')
    }


def render_comment(comment):
    if comment is None:
        return {}
    return {
        'url': get_object_url(comment.AboutPost.experience),
        'user': render_user(comment.OwnerUser),
        'post': render_experience(comment.AboutPost.experience),
        'text': comment.Text,
        'date_created': comment.DateCreated.strftime('%s')
    }


def render_item(item):
    if item is None:
        return {}
    return {
        'name': item.Name,
        'price': item.Price,
        'currency': item.Currency.Code,
        'date_created': item.DateCreated.strftime('%s')
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
        'date_created': gallery_item.DateCreated.strftime('%s')
    }


def render_notification(notification):
    if notification is None:
        return {}
    result = {
        'from_user': render_user(notification.FromUser),
        'is_read': notification.IsRead,
        'type': NotificationType.values[notification.Type],
        'date_created': notification.DateCreated.strftime('%s'),
        'mark_as_read_url': get_custom_url(api_urls['JSON_URL_MARK_NOTIFICATION_AS_READ'], IntToBase62(notification.pk)),
        'mark_as_unread_url': get_custom_url(api_urls['JSON_URL_MARK_NOTIFICATION_AS_UNREAD'], IntToBase62(notification.pk)),
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
        'user': render_user(event.OwnerUser),
        'event_type': EventType.values[event.EventType],
        'date_created': event.DatePublished.strftime('%s')
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
