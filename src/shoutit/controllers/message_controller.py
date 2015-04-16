from django.contrib.contenttypes.models import ContentType
from django.db import IntegrityError
from common.constants import MESSAGE_ATTACHMENT_TYPE_SHOUT, CONVERSATION_TYPE_CHAT, CONVERSATION_TYPE_ABOUT_SHOUT
from common.constants import MESSAGE_ATTACHMENT_TYPE_LOCATION

from shoutit.models import MessageAttachment, Shout, Conversation, Message, MessageDelete, MessageRead, SharedLocation
from shoutit.controllers import notifications_controller


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

    if not conversation:
        if about:
            conversation = Conversation.objects.create(attached_object=about, type=CONVERSATION_TYPE_ABOUT_SHOUT)
        else:
            conversation = Conversation.objects.create(type=CONVERSATION_TYPE_CHAT)
        conversation.users = to_users

    # add the new message
    message = Message.objects.create(conversation=conversation, user=user, text=text)

    # read it
    MessageRead.objects.create(user=user, message=message, conversation=conversation)

    # update the conversation
    conversation.last_message = message
    conversation.save()

    if not attachments:
        attachments = []

    for attachment in attachments:
        # todo: map the content types to models
        if MESSAGE_ATTACHMENT_TYPE_SHOUT.text in attachment:
            object_id = attachment[MESSAGE_ATTACHMENT_TYPE_SHOUT.text]['id']
            content_type = ContentType.objects.get_for_model(Shout)
            ma_type = MESSAGE_ATTACHMENT_TYPE_SHOUT
            MessageAttachment(message_id=message.id, conversation_id=conversation.id, content_type=content_type, object_id=object_id,
                              type=ma_type).save()

        if MESSAGE_ATTACHMENT_TYPE_LOCATION.text in attachment:
            location = attachment['location']
            sl = SharedLocation(latitude=location['latitude'], longitude=location['longitude'])
            sl.save()
            object_id = sl.id
            content_type = ContentType.objects.get_for_model(SharedLocation)
            ma_type = MESSAGE_ATTACHMENT_TYPE_LOCATION
            MessageAttachment(message_id=message.id, conversation_id=conversation.id, content_type=content_type, object_id=object_id,
                              type=ma_type).save()

    for to_user in conversation.contributors:
        if user != to_user:
            notifications_controller.notify_user_of_message(to_user, message, request)

    return message
