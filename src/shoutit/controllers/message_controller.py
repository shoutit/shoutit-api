from __future__ import unicode_literals
from django.contrib.contenttypes.models import ContentType
from django.db import IntegrityError
from common.constants import (MESSAGE_ATTACHMENT_TYPE_SHOUT, CONVERSATION_TYPE_CHAT, CONVERSATION_TYPE_ABOUT_SHOUT,
                              MESSAGE_ATTACHMENT_TYPE_MEDIA)
from common.constants import MESSAGE_ATTACHMENT_TYPE_LOCATION
from common.utils import any_in
from shoutit.models import (MessageAttachment, Shout, Conversation, Message, MessageDelete, SharedLocation,
                            Video)
from shoutit.controllers import notifications_controller
from shoutit.utils import error_logger


def get_conversation(conversation_id):
    try:
        return Conversation.objects.get(pk=conversation_id)
    except Conversation.DoesNotExist:
        return None


def get_message(message_id):
    try:
        return Message.objects.get(pk=message_id)
    except Message.DoesNotExist:
        return None


def conversation_exist(conversation_id=None, users=None, about=None):
    """
    Check whether a conversation with same id or both users and about exists
    """
    if conversation_id:
        return get_conversation(conversation_id) or False
    elif users:
        assert isinstance(users, list)
        # remove duplicates if any
        users = list(set(users))

        if about:
            conversations = Conversation.objects.with_attached_object(about)
        else:
            conversations = Conversation.objects.filter(object_id=None)

        for user in users:
            conversations = conversations.filter(users=user)
        return conversations[0] if len(conversations) else False
    else:
        return False


def hide_message_from_user(message, user):
    try:
        MessageDelete(user=user, message_id=message.id, conversation_id=message.conversation.id).save(True)
    except IntegrityError:
        pass


def send_message(conversation, user, to_users=None, about=None, text=None, attachments=None, request=None):
    assert conversation or to_users, "Either an existing conversation or a list of to_users should be provided to create a message."

    if to_users and isinstance(to_users, list):
        # conversation users include everyone in it
        to_users.append(user)

    if not conversation:
        conversation = conversation_exist(users=to_users, about=about)

    # creator_id is temp attributes used only for tracking
    if not conversation:
        if about:
            conversation = Conversation(attached_object=about, type=CONVERSATION_TYPE_ABOUT_SHOUT)
        else:
            conversation = Conversation(type=CONVERSATION_TYPE_CHAT)
        conversation.creator_id = user.pk
        conversation.save()
        conversation.users.add(*to_users)

    # add the new message
    if text:
        text = text[:2000]
    if not attachments:
        attachments = []
    message = Message(conversation=conversation, user=user, text=text)
    message.raw_attachments = attachments
    message.request = request
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
                except Exception as e:
                    error_logger.warn("Error creating video", exc_info=True, extra={'detail': str(e), 'video': v})
