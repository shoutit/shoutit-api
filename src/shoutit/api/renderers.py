from django.contrib.contenttypes.models import ContentType

from shoutit.api.api_utils import get_custom_url, get_object_api_url, api_urls, JSON_URL_MARK_NOTIFICATION_AS_READ, \
    JSON_URL_MARK_NOTIFICATION_AS_UNREAD
from common.constants import *
from common.utils import date_unix
from shoutit.models import User, Profile, Business, Tag, Message2, Trade, MessageAttachment, SharedLocation


# todo: better levels
from shoutit.utils import full_url_path, shout_link, tag_link, user_link


def render_shout(shout, level=5):
    """
    :type shout: Trade
    """
    if not isinstance(shout, Trade):
        return {}

    images = [image.image for image in shout.get_images()]
    videos = [render_video(video) for video in shout.get_videos()]
    tags = [render_tag(tag) for tag in shout.get_tags()]

    shout_json = {
        'id': shout.pk,
        'type': PostType.values[shout.type],
        'name': None if shout.type == POST_TYPE_EXPERIENCE else shout.item.name,
        'description': shout.text,
        'price': None if shout.type == POST_TYPE_EXPERIENCE else shout.item.Price,
        'currency': None if shout.type == POST_TYPE_EXPERIENCE else shout.item.Currency.Code,
        'thumbnail': videos[0]['thumbnail_url'] if videos else shout.get_first_image().image if images else '',
        'date_created': shout.date_published.strftime('%s'),
        'api_url': get_object_api_url(shout),
        'web_url': shout_link(shout),
        'user': render_user(shout.user, level=2),
        'location': {
            'country': shout.country,
            'city': shout.city,
            'latitude': shout.latitude,
            'longitude': shout.longitude,
            'address': shout.address
        }
    }

    if level >= 2:
        shout_json.update({
            'images': images,
            'videos': videos,
            'tags': tags,
        })

    return shout_json


def render_tag(tag):
    if tag is None:
        return {}
    if isinstance(tag, basestring):
        tag = Tag(name=tag)
    # TODO: find what is the case when tag is a dict not instance of Tag class
    elif isinstance(tag, dict):
        tag = Tag(name=tag['name'])
    base = {
        'name': tag.name,
        'api_url': get_object_api_url(tag),
        'web_url': tag_link(tag),
        'image': full_url_path(tag.image)
    }
    return base


def render_tag_dict(tag_dict):
    tag = {
        'name': tag_dict['name'],
        'api_url': full_url_path('/tags/%s/' % tag_dict['name']),
        'web_url': tag_link(tag_dict),
        'image': full_url_path(tag_dict['image'])
    }
    if 'is_listening' in tag_dict:
        tag['is_listening'] = tag_dict['is_listening']

    if 'listeners_count' in tag_dict:
        tag['listeners_count'] = tag_dict['listeners_count']

    return tag


# TODO: rendering levels in better way.
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
        from shoutit.controllers.user_controller import get_profile

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
            'id': user.pk,
            'name': user.name,
            'username': user.username,
            'first_name': user.first_name,
            'last_name': user.last_name,
        }

        if level >= 2:
            result.update({
                'api_url': get_object_api_url(user),
                'web_url': user_link(user),
                'is_active': user.is_active,
                'image': full_url_path(profile.image),
                'sex': profile.Sex,
            })
            if profile.video:
                result.update({
                    'video': render_video(profile.video),
                })
        if level >= 3:
            result.update({
                'date_joined': date_unix(user.date_joined),
                'bio': profile.Bio,
                'location': {
                    'country': profile.country,
                    'city': profile.city

                }
            })
            if owner:
                result['location'].update({
                    'latitude': profile.latitude,
                    'longitude': profile.longitude
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
            # todo: other business attributes
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
        'text': message.text,
        'is_read': message.is_read,
        'date_created': message.DateCreated.strftime('%s'),
        # 'attachments': [render_message_attachment(attachment) for attachment in message.attachments.all()],
    }


def render_message2(message):
    """
    :type message: Message2
    """
    if not isinstance(message, Message2):
        return {}

    return {
        'id': message.pk,
        'conversation': {
            'id': message.conversation.pk
        },
        'user': render_user(message.user, level=1),
        'message': message.text,
        'created_at': message.created_at_unix,
        'attachments': [render_message_attachment(attachment) for attachment in message.attachments.all()],
    }


def render_message_attachment(message_attachment):
    """
    :type message_attachment: MessageAttachment
    """
    if not isinstance(message_attachment, MessageAttachment):
        return {}

    shout_ct = ContentType.objects.get_for_model(Trade)
    location_ct = ContentType.objects.get_for_model(SharedLocation)

    if message_attachment.content_type == shout_ct:
        result = {
            'content_type': 'shout',
            'object_id': message_attachment.object_id,
            'shout': render_shout(message_attachment.attached_object, level=1)
        }

    elif message_attachment.content_type == location_ct:
        result = {
            'content_type': 'location',
            'location': {
                'latitude': message_attachment.attached_object.latitude,
                'longitude': message_attachment.attached_object.longitude,
            }
        }
    else:
        result = {}

    return result


def render_conversation(conversation):
    if not conversation:
        return {}
    return {
        'conversation_id': conversation.pk,
        'api_url': get_object_api_url(conversation),
        'from_user': render_user(conversation.FromUser, level=2),
        'to_user': render_user(conversation.ToUser, level=2),
        'about': render_shout(conversation.AboutPost, level=1),
        'is_read': conversation.is_read,
        'text': conversation.text if hasattr(conversation, 'text') else '',
        'date_created': hasattr(conversation, 'DateCreated') and conversation.DateCreated.strftime('%s') or None
    }


def render_conversation2(conversation):
    """
    :type conversation: Conversation2
    """
    obj = {
        'id': conversation.pk,
        'api_url': get_object_api_url(conversation),
        'users': [render_user(user, level=2) for user in conversation.contributors],
        'last_message': render_message2(conversation.last_message),
        'modified_at': conversation.modified_at_unix,
    }
    if conversation.object_id:
        obj['attached_object'] = render_shout(conversation.attached_object, level=1),
    return obj


def render_conversation_full(conversation):
    if conversation is None:
        return {}
    return {
        'api_url': get_object_api_url(conversation),
        'from_user': render_user(conversation.FromUser, level=2),
        'to_user': render_user(conversation.ToUser, level=2),
        'about': render_shout(conversation.AboutPost),
        'is_read': conversation.is_read,
        'text': conversation.text if hasattr(conversation, 'text') else '',
        'conversation_messages': [render_message(message) for message in conversation.messages],
        'date_created': hasattr(conversation, 'DateCreated') and conversation.DateCreated.strftime('%s') or None
    }


def render_experience(experience):
    if experience is None:
        return {}
    else:
        rendered_experience = {
            'id': experience.pk,
            'api_url': get_object_api_url(experience),
            'user': render_user(experience.user),
            'business': render_user(experience.AboutBusiness),
            'state': experience.State,
            'text': experience.text,
            'date_created': experience.date_published.strftime('%s'),
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
        'api_url': get_object_api_url(shared.Experience),
        'user': render_user(shared.user),
        'experience': render_experience(shared.Experience),
        'date_created': shared.DateCreated.strftime('%s')
    }


def render_comment(comment):
    if comment is None:
        return {}
    return {
        'api_url': get_object_api_url(comment.AboutPost.experience),
        'user': render_user(comment.user),
        'post': render_experience(comment.AboutPost.experience),
        'text': comment.text,
        'date_created': comment.DateCreated.strftime('%s')
    }


def render_item(item):
    if item is None:
        return {}
    return {
        'name': item.name,
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
        # 'url' : get_object_api_url(gallery),
        #		'business' : render_business(gallery.business),
    }


def render_gallery_item(gallery_item):
    if gallery_item is None:
        return {}
    return {
        'url': '/gallery_items/%s/' % gallery_item.Gallery.business.user.username,
        'item': render_item(gallery_item.item),
        'gallery': render_gallery(gallery_item.Gallery),
        'date_created': gallery_item.DateCreated.strftime('%s')
    }


def render_notification(notification):
    if notification is None:
        return {}
    result = {
        'from_user': render_user(notification.FromUser, level=2),
        'is_read': notification.is_read,
        'type': NotificationType.values[notification.type],
        'date_created': notification.DateCreated.strftime('%s'),
        'mark_as_read_url': get_custom_url(api_urls[JSON_URL_MARK_NOTIFICATION_AS_READ], notification.pk),
        'mark_as_unread_url': get_custom_url(api_urls[JSON_URL_MARK_NOTIFICATION_AS_UNREAD], notification.pk),
        'id': notification.pk
    }

    if notification.attached_object:
        if notification.type == NOTIFICATION_TYPE_MESSAGE:
            result['attached_object'] = render_message(notification.attached_object)
        elif notification.type == NOTIFICATION_TYPE_LISTEN:
            result['attached_object'] = render_user(notification.attached_object, level=2)
        elif notification.type == NOTIFICATION_TYPE_EXP_POSTED:
            result['attached_object'] = render_experience(notification.attached_object)
        elif notification.type == NOTIFICATION_TYPE_EXP_SHARED:
            result['attached_object'] = render_shared_exp(notification.attached_object)
        elif notification.type == NOTIFICATION_TYPE_COMMENT:
            result['attached_object'] = render_comment(notification.attached_object)
    return result


def render_event(event):
    if event is None:
        return {}
    result = {
        'user': render_user(event.user, level=2),
        'event_type': EventType.values[event.EventType],
        'date_created': event.date_published.strftime('%s')
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
        # elif event.EventType == EVENT_TYPE_GALLERY_ITEM :
        #			result['attached_object'] = render_gallery_item(event.attached_object)
        #		elif event.EventType == EVENT_TYPE_POST_DEAL or event.EventType == EVENT_TYPE_BUY_DEAL :
        #			result['attached_object'] = render_deal(event.attached_object)
        return result


def render_currency(currency):
    return {
        'code': currency.Code,
        'name': currency.name,
        'country': currency.country
    }


def render_post(post):
    if post.type == POST_TYPE_REQUEST or post.type == POST_TYPE_OFFER:
        return render_shout(post)
    # elif post.type == POST_TYPE_DEAL:
    #		return render_deal(post)
    elif post.type == POST_TYPE_EVENT:
        return render_event(post)
    elif post.type == POST_TYPE_EXPERIENCE:
        return render_experience(post)
    else:
        return {}
