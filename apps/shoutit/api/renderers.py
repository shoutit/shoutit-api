from apps.shoutit.api.api_utils import get_custom_url, get_object_url, api_urls
from common.constants import *
from apps.shoutit.models import User, Profile, Business, Tag


# todo: better levels
from apps.shoutit.utils import full_url_path


def render_shout(shout, level=5):
    images = [image.Image for image in shout.get_images()]
    videos = [render_video(video) for video in shout.get_videos()]
    tags = [render_tag(tag) for tag in shout.get_tags()]

    shout_json = {
        'id': shout.pk,
        'type': PostType.values[shout.Type],
        'name': None if shout.Type == POST_TYPE_EXPERIENCE else shout.Item.Name,
        'description': shout.Text,
        'price': None if shout.Type == POST_TYPE_EXPERIENCE else shout.Item.Price,
        'currency': None if shout.Type == POST_TYPE_EXPERIENCE else shout.Item.Currency.Code,
        'thumbnail':  videos[0]['thumbnail_url'] if videos else shout.get_first_image().Image if images else '',
        'date_created': shout.DatePublished.strftime('%s'),
        'url': get_object_url(shout),
        'user': render_user(shout.OwnerUser, level=2),
    }

    if level >= 2:
        shout_json.update({
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

        })

    return shout_json


def render_tag(tag):
    if tag is None:
        return {}
    if isinstance(tag, basestring):
        tag = Tag(Name=tag)
    # TODO: find what is the case when tag is a dict not instance of Tag class
    elif isinstance(tag, dict):
        tag = Tag(Name=tag['Name'])
    base = {
        'name': tag.Name,
        'url': get_object_url(tag),
        'image': full_url_path(tag.Image)
    }
    return base


def render_tag_dict(tag_dict):
    tag = {
        'name': tag_dict['Name'],
        'url': full_url_path('/tag/%s/' % tag_dict['Name']),
        'image': full_url_path(tag_dict['Image'])
    }
    if 'is_listening' in tag_dict:
        tag['is_listening'] = tag_dict['is_listening']

    if 'listeners_count' in tag_dict:
        tag['listeners_count'] = tag_dict['listeners_count']

    return tag


#TODO: rendering levels in better way.
# 1: username and name
# 2: url, image, video, sex, is_active
# 3: date_joined, bio, location
# 4: email, social_channels
# 5: push tokens
# todo: enhanced function for rendering array of users/profiles/businesses
def render_user(user, level=1, owner=False):
    if user is None:
        return {}

    profile = None
    result = {}
    if isinstance(user, basestring):
        # todo: fix import
        from apps.shoutit.controllers.user_controller import get_profile
        profile = get_profile(user)

    elif isinstance(user, User):
        try:
            profile = user.profile
        except AttributeError:
            profile = user.business

    elif isinstance(user, (Profile, Business)):
        profile = user
        user = user.user

    if isinstance(profile, Profile):

        result = {
            'name': user.name,
            'username': user.username
        }

        if level >= 2:
            result.update({
                'url': get_object_url(user),
                'image': full_url_path(profile.Image),
                'video': render_video(profile.video),
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
        if level >= 4:
            result.update({
                'email': user.email,
                'social_channels': {
                    'facebook': True if (hasattr(user, 'linked_facebook') and user.linked_facebook) else False,
                    'gplus': True if (hasattr(user, 'linked_gplus') and user.linked_gplus) else False
                }
            })

        if level >= 5:
            result.update({
                'push_tokens': {
                    'apns': user.apns_device.registration_id if user.apns_device else None,
                    'gcm': user.gcm_device.registration_id if user.gcm_device else None
                }
            })

    elif isinstance(profile, Business):
        result = {
            #todo: other business attributes
        }
    return result


def render_message(message):
    if not message:
        return {}

    return {
        'message_id': message.pk,
        'conversation_id': message.Conversation.pk,
        'shout_id': message.Conversation.AboutPost.pk,
        'from_user': render_user(message.FromUser, level=1),
        'to_user': render_user(message.ToUser, level=1),
        'text': message.Text,
        'is_read': message.IsRead,
        'date_created': message.DateCreated.strftime('%s'),
        'attachments': [render_message_attachment(attachment) for attachment in message.attachments.all()],
    }


def render_message_attachment(message_attachment):
    if not message_attachment:
        return {}
    content_type = 'shout'  # todo: possible other content types, therefore other content object
    attached_object = render_shout(message_attachment.attached_object, level=1)
    return {
        'content_type': content_type,
        'object_id': message_attachment.object_id,
        content_type: attached_object
    }


def render_conversation(conversation):
    if not conversation:
        return {}
    return {
        'conversation_id': conversation.pk,
        'url': get_object_url(conversation),
        'from_user': render_user(conversation.FromUser, level=2),
        'to_user': render_user(conversation.ToUser, level=2),
        'about': render_shout(conversation.AboutPost, level=1),
        'is_read': conversation.IsRead,
        'text': conversation.Text if hasattr(conversation, 'Text') else '',
        'date_created': hasattr(conversation, 'DateCreated') and conversation.DateCreated.strftime('%s') or None
    }


def render_conversation_full(conversation):
    if conversation is None:
        return {}
    return {
        'url': get_object_url(conversation),
        'from_user': render_user(conversation.FromUser, level=2),
        'to_user': render_user(conversation.ToUser, level=2),
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
            'id': experience.pk,
            'url': get_object_url(experience),
            'user': render_user(experience.OwnerUser),
            'business': render_user(experience.AboutBusiness),
            'state': experience.State,
            'text': experience.Text,
            'date_created': experience.DatePublished.strftime('%s'),
            'detailed': experience.detailed if hasattr(experience, 'detailed') else False
        }

        if hasattr(experience, 'detailed') and experience.detailed:
            rendered_experience.update({
                'details': {
                    'users_shared_experiences': [render_user(user) for user in experience.usersSharedExperience],
                    'comments': [render_comment(comment) for comment in experience.comments],
                    'shared_experiences_count': experience.sharedExpsCount,
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
        'url': '/gallery_items/%s/' % gallery_item.Gallery.OwnerBusiness.user.username,
        'item': render_item(gallery_item.Item),
        'gallery': render_gallery(gallery_item.Gallery),
        'date_created': gallery_item.DateCreated.strftime('%s')
    }


def render_notification(notification):
    if notification is None:
        return {}
    result = {
        'from_user': render_user(notification.FromUser, level=2),
        'is_read': notification.IsRead,
        'type': NotificationType.values[notification.Type],
        'date_created': notification.DateCreated.strftime('%s'),
        'mark_as_read_url': get_custom_url(api_urls['JSON_URL_MARK_NOTIFICATION_AS_READ'], notification.pk),
        'mark_as_unread_url': get_custom_url(api_urls['JSON_URL_MARK_NOTIFICATION_AS_UNREAD'], notification.pk),
        'id': notification.pk
    }

    if notification.attached_object:
        if notification.Type == NOTIFICATION_TYPE_MESSAGE:
            result['attached_object'] = render_message(notification.attached_object)
        elif notification.Type == NOTIFICATION_TYPE_LISTEN:
            result['attached_object'] = render_user(notification.attached_object, level=2)
        elif notification.Type == NOTIFICATION_TYPE_EXP_POSTED:
            result['attached_object'] = render_experience(notification.attached_object)
        elif notification.Type == NOTIFICATION_TYPE_EXP_SHARED:
            result['attached_object'] = render_shared_exp(notification.attached_object)
        elif notification.Type == NOTIFICATION_TYPE_COMMENT:
            result['attached_object'] = render_comment(notification.attached_object)
    return result


def render_event(event):
    if event is None:
        return {}
    result = {
        'user': render_user(event.OwnerUser, level=2),
        'event_type': EventType.values[event.EventType],
        'date_created': event.DatePublished.strftime('%s')
    }

    if event.attached_object:
        if event.EventType == EVENT_TYPE_FOLLOW_USER:
            result['attached_object'] = render_user(event.attached_object, level=2)
        elif event.EventType == EVENT_TYPE_FOLLOW_TAG:
            result['attached_object'] = render_tag(event.attached_object)
        elif event.EventType == EVENT_TYPE_SHOUT_OFFER or event.EventType == EVENT_TYPE_SHOUT_REQUEST:
            result['attached_object'] = render_shout(event.attached_object)
        elif event.EventType == EVENT_TYPE_EXPERIENCE:
            result['attached_object'] = render_experience(event.attached_object)
        elif event.EventType == EVENT_TYPE_SHARE_EXPERIENCE:
            result['attached_object'] = render_shared_exp(event.attached_object)
        elif event.EventType == EVENT_TYPE_COMMENT:
            result['attached_object'] = render_comment(event.attached_object)
        #		elif event.EventType == EVENT_TYPE_GALLERY_ITEM :
        #			result['attached_object'] = render_gallery_item(event.attached_object)
        #		elif event.EventType == EVENT_TYPE_POST_DEAL or event.EventType == EVENT_TYPE_BUY_DEAL :
        #			result['attached_object'] = render_deal(event.attached_object)
        return result


def render_currency(currency):
    return {
        'code': currency.Code,
        'name': currency.Name,
        'country': currency.Country
    }


def render_post(post):
    if post.Type == POST_TYPE_REQUEST or post.Type == POST_TYPE_OFFER:
        return render_shout(post)
    #	elif post.Type == POST_TYPE_DEAL:
    #		return render_deal(post)
    elif post.Type == POST_TYPE_EVENT:
        return render_event(post)
    elif post.Type == POST_TYPE_EXPERIENCE:
        return render_experience(post)
    else:
        return {}
