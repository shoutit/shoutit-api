from __future__ import unicode_literals

from django.contrib.contenttypes.models import ContentType
from django.db import IntegrityError, transaction
from django.db.models import Count
from pydash import arrays

from common.constants import MESSAGE_ATTACHMENT_TYPE_LOCATION, MESSAGE_ATTACHMENT_TYPE_PROFILE
from common.constants import (MESSAGE_ATTACHMENT_TYPE_SHOUT, CONVERSATION_TYPE_CHAT, CONVERSATION_TYPE_ABOUT_SHOUT,
                              MESSAGE_ATTACHMENT_TYPE_MEDIA, CONVERSATION_TYPE_PUBLIC_CHAT)
from common.utils import any_in
from shoutit.controllers import location_controller
from shoutit.models import (Conversation, Message, MessageAttachment, MessageDelete, Shout, User, SharedLocation,
                            Video)
from shoutit.utils import error_logger


def conversation_exist(conversation_id=None, users=None, about=None, include_public=False):
    """
    Check whether a conversation with same id or both users and about exists
    """
    if conversation_id:
        try:
            return Conversation.objects.get(pk=conversation_id)
        except Conversation.DoesNotExist:
            return False

    elif users:
        assert isinstance(users, list)

        if about:
            conversations = Conversation.objects.with_attached_object(about)
        else:
            conversations = Conversation.objects.filter(object_id=None)

        if not include_public:
            conversations = conversations.exclude(type=CONVERSATION_TYPE_PUBLIC_CHAT)

        users = arrays.unique(users)
        conversations = conversations.annotate(c=Count('users')).filter(c=len(users))
        for user in users:
            conversations = conversations.filter(users=user)
        return conversations.first() or False
    else:
        return False


def hide_message_from_user(message, user):
    try:
        with transaction.atomic():
            MessageDelete(user=user, message_id=message.id, conversation_id=message.conversation.id).save(True)
    except IntegrityError:
        pass


def hide_messages_from_user(messages, user):
    for message in messages:
        hide_message_from_user(message, user)


def send_message(conversation, user, to_users=None, about=None, text=None, attachments=None, request=None,
                 page_admin_user=None):
    assert conversation or to_users, "Either an existing conversation or a list of to_users should be provided to create a message."

    if to_users and isinstance(to_users, list):
        # conversation users include everyone in it
        to_users.append(user)

    if not conversation:
        conversation = conversation_exist(users=to_users, about=about)

    if not conversation:
        if about:
            extra = {'type': CONVERSATION_TYPE_ABOUT_SHOUT, 'attached_object': about}
        else:
            extra = {'type': CONVERSATION_TYPE_CHAT}
        conversation = Conversation.create(creator=user, **extra)
        conversation.users.add(*to_users)

    # add the new message
    if text:
        text = text[:2000]
    if not attachments:
        attachments = []
    message = Message(conversation=conversation, user=user, text=text, page_admin_user=page_admin_user)
    message.raw_attachments = attachments
    message.request = request
    message.api_client = getattr(request, 'api_client', None)
    message.api_version = getattr(request, 'version', None)
    message.save()
    return message


def save_message_attachments(message, attachments):
    conversation = message.conversation
    for attachment in attachments:
        # todo: map the content types to models
        if MESSAGE_ATTACHMENT_TYPE_SHOUT.text in attachment:
            object_id = attachment[MESSAGE_ATTACHMENT_TYPE_SHOUT.text]['id']
            content_type = ContentType.objects.get_for_model(Shout)
            ma_type = MESSAGE_ATTACHMENT_TYPE_SHOUT
            MessageAttachment.create(message_id=message.id, conversation_id=conversation.id, content_type=content_type,
                                     object_id=object_id, type=ma_type).save()

        if MESSAGE_ATTACHMENT_TYPE_PROFILE.text in attachment:
            object_id = attachment[MESSAGE_ATTACHMENT_TYPE_PROFILE.text]['id']
            content_type = ContentType.objects.get_for_model(User)
            ma_type = MESSAGE_ATTACHMENT_TYPE_PROFILE
            MessageAttachment.create(message_id=message.id, conversation_id=conversation.id, content_type=content_type,
                                     object_id=object_id, type=ma_type).save()

        if MESSAGE_ATTACHMENT_TYPE_LOCATION.text in attachment:
            location = attachment['location']
            sl = SharedLocation(latitude=location['latitude'], longitude=location['longitude'])
            sl.save()
            object_id = sl.id
            content_type = ContentType.objects.get_for_model(SharedLocation)
            ma_type = MESSAGE_ATTACHMENT_TYPE_LOCATION
            MessageAttachment.create(message=message, conversation=conversation, content_type=content_type,
                                     object_id=object_id, type=ma_type)

        if any_in(['images', 'videos'], attachment):
            ma_type = MESSAGE_ATTACHMENT_TYPE_MEDIA
            images = attachment.get('images', []) or []
            videos = attachment.get('videos', []) or []
            ma = MessageAttachment.create(type=ma_type, message=message, conversation=conversation, images=images)
            for v in videos:
                # todo: better handling
                try:
                    video = Video.create(url=v['url'], thumbnail_url=v['thumbnail_url'], provider=v['provider'],
                                         id_on_provider=v['id_on_provider'], duration=v['duration'])
                    ma.videos.add(video)
                except Exception:
                    error_logger.warn("Error creating video", exc_info=True)


def create_public_chat(creator, subject, icon=None, location=None):
    conversation = Conversation(creator=creator, type=CONVERSATION_TYPE_PUBLIC_CHAT, subject=subject, icon=icon)
    if location:
        location_controller.update_object_location(conversation, location, save=False)
    conversation.save()
    conversation.users.add(creator)
    return conversation
