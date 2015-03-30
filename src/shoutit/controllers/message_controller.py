from datetime import datetime

from django.contrib.contenttypes.models import ContentType
from django.db import IntegrityError
from django.db.models.aggregates import Max
from django.db.models.query_utils import Q
from common.constants import MESSAGE_ATTACHMENT_TYPE_SHOUT, CONVERSATION_TYPE_CHAT, CONVERSATION_TYPE_ABOUT_SHOUT
from common.constants import MESSAGE_ATTACHMENT_TYPE_LOCATION

from shoutit.models import Conversation, Message, MessageAttachment, Tag, StoredImage, Trade, Conversation2, Message2, \
    Conversation2Delete, Message2Delete, Message2Read, SharedLocation
from shoutit.controllers import shout_controller, email_controller, notifications_controller


def conversation_exist(conversation_id=None, user1=None, user2=None, about=None):
    try:
        if conversation_id:
            return Conversation.objects.get(pk=conversation_id)
        elif user1 and user2 and about:
            return Conversation.objects.get(
                Q(AboutPost=about) & ((Q(FromUser=user1) & Q(ToUser=user2)) | (Q(FromUser=user2) & Q(ToUser=user1)))
            )
        else:
            return False
    except Conversation.DoesNotExist:
        return False


def send_message(from_user, to_user, about, text=None, conversation=None):
    if not conversation:
        conversation = conversation_exist(user1=from_user, user2=to_user, about=about)

    if not conversation:
        conversation = Conversation(FromUser=from_user, ToUser=to_user, AboutPost=about)

    # todo: fix visibility to sender receiver!?
    conversation.is_read = False
    conversation.VisibleToSender = True
    conversation.VisibleToRecivier = True
    conversation.save()

    message = Message(Conversation=conversation, FromUser=from_user, ToUser=to_user, text=text if text else None)
    message.save()

    # removed attachment from old messages

    notifications_controller.notify_user_of_message(to_user, message)
    email_controller.send_message_email(message)

    # future compatibility
    message2_from_message(message)
    return message


# todo: deprecate in favor of messaging 2
def getFullConversationDetails(conversations, user):
    result_conversations = []
    conversation_ids = [conversation.pk for conversation in conversations]
    conversations_messages = Message.objects.filter(Q(Conversation__pk__in=conversation_ids) & (
        (Q(FromUser=user) & Q(VisibleToSender=True)) | (Q(ToUser=user) & Q(VisibleToRecivier=True)))).select_related(
        'Conversation', 'ToUser', 'ToUser__profile', 'FromUser', 'FromUser__profile').order_by('DateCreated')
    shout_pks = [conversation.AboutPost.pk for conversation in conversations]

    if shout_pks:
        tags = Tag.objects.select_related('Creator').prefetch_related('shouts')
        tags = tags.extra(where=['shout_id IN (%s)' % ','.join(["'%s'" % str(shout_pk) for shout_pk in shout_pks])])
        tags_with_shout_id = list(tags.values('pk', 'name', 'Creator', 'image', 'DateCreated', 'Definition', 'shouts__pk'))

    else:
        tags_with_shout_id = []

    images = StoredImage.objects.filter(item__pk__in=[conversation.AboutPost.item.pk for conversation in conversations]).order_by('image')

    empty_conversations_to = []
    empty_conversations_from = []
    for conversation in conversations:
        conversation.messages = [message for message in conversations_messages if message.Conversation.pk == conversation.pk]
        if not len(conversation.messages):
            if conversation.FromUser == user:
                empty_conversations_from.append(conversation.pk)
            else:
                empty_conversations_to.append(conversation.pk)
            continue
        conversation.AboutPost.set_images([image for image in images if image.item.pk == conversation.AboutPost.item.pk])
        conversation.AboutPost.set_tags([tag for tag in tags_with_shout_id if str(tag['shouts__pk']) == conversation.AboutPost.pk])
        last_message = list(conversation.messages)[-1]
        conversation.text = last_message.text[0:256] if last_message.text else "attachment"
        conversation.DateCreated = list(conversation.messages)[-1].DateCreated
        conversation.With = conversation.FromUser if conversation.FromUser != user else conversation.ToUser
        conversation.is_read = False if [1 if message.ToUser == user and not message.is_read else 0 for message in
                                        conversation.messages].count(1) else True
        result_conversations.append(conversation)

    Conversation.objects.filter(pk__in=empty_conversations_from).update(VisibleToSender=False)
    Conversation.objects.filter(pk__in=empty_conversations_to).update(VisibleToRecivier=False)
    return result_conversations


def ReadConversations(user, start_index=None, end_index=None):
    conversations = Conversation.objects.filter(
        ((Q(FromUser=user) & Q(VisibleToSender=True)) | (Q(ToUser=user) & Q(VisibleToRecivier=True)))
    ).select_related('FromUser',
                     'FromUser__profile',
                     'ToUser',
                     'ToUser__profile',
                     'AboutPost',
                     'AboutPost__item',
                     'AboutPost__item__Currency',
                     'AboutPost__user',
                     'AboutPost__user__profile').annotate(max_date=Max('Messages__DateCreated')).order_by(
        '-max_date')[start_index:end_index]
    return getFullConversationDetails(conversations, user)


def ReadConversation(user, conversation_id):
    conversation = Conversation.objects.get(pk=conversation_id)
    Message.objects.filter(Q(Conversation=conversation) & (Q(FromUser=user) | Q(ToUser=user))).update(is_read=True)
    messages = Message.objects.filter(
        Q(Conversation=conversation) & ((Q(FromUser=user) & Q(VisibleToSender=True)) | (Q(ToUser=user) & Q(VisibleToRecivier=True)))
    ).order_by('DateCreated')
    # future compatibility
    read_conversation2(user, conversation)
    return messages


def get_conversation(conversation_id, user=None):
    try:
        conversation = Conversation.objects.get(pk=conversation_id)
    except Conversation.DoesNotExist:
        conversation = None

    if not conversation:
        return None

    if not user:
        return conversation
    else:
        full_conversations = getFullConversationDetails([conversation], user)
        full_conversation = full_conversations[0] if len(full_conversations) else None
        return full_conversation or conversation


def get_shout_conversations(shout_id, user):
    # todo: simplify
    shout = shout_controller.get_post(shout_id, True, True)
    if user.is_authenticated() and user.pk == shout.user.pk:
        conversations = Conversation.objects.filter(AboutPost=shout, ToUser=user, VisibleToRecivier=True).annotate(
            max_date=Max('Messages__DateCreated')).select_related('ToUser', 'ToUser__profile', 'FromUser',
                                                                  'FromUser__profile', 'AboutPost', 'AboutPost__item',
                                                                  'AboutPost__item__Currency',
                                                                  ).order_by('-max_date')
        conversations = getFullConversationDetails(conversations, user)
    elif user.is_authenticated():
        conversations = Conversation.objects.filter(AboutPost=shout, FromUser=user, VisibleToSender=True).annotate(
            max_date=Max('Messages__DateCreated')).select_related('ToUser', 'ToUser__profile', 'FromUser',
                                                                  'FromUser__profile', 'AboutPost', 'AboutPost__item',
                                                                  'AboutPost__item__Currency',
                                                                  ).order_by('-max_date')
        conversations = getFullConversationDetails(conversations, user)
    else:
        conversations = []

    return conversations


def hide_message_from_user(message, user):
    if user == message.FromUser:
        message.VisibleToSender = False
    else:
        message.VisibleToRecivier = False
    message.save()

    # future compatibility
    hide_message2_from_user(message, user)


def get_message(message_id):
    try:
        return Message.objects.get(pk=message_id)
    except Message.DoesNotExist:
        return None


def hide_conversation_from_user(conversation, user):
    if user == conversation.FromUser:
        conversation.VisibleToSender = False
    else:
        conversation.VisibleToRecivier = False
    conversation.save()

    # future compatibility
    hide_conversation2_from_user(conversation, user)


def ConversationsCount(user):
    return Conversation.objects.filter(
        (Q(FromUser=user) & Q(VisibleToSender=True)) | (Q(ToUser=user) & Q(VisibleToRecivier=True))).count()


def UnReadConversationsCount(user):
    return Conversation.objects.filter(Q(Messages__ToUser=user) & Q(Messages__is_read=False) & (
        (Q(FromUser=user) & Q(VisibleToSender=True)) | (Q(ToUser=user) & Q(VisibleToRecivier=True)))).values(
        "pk").distinct().count()


# ######################################## #
# ############### M2 ##################### #


def get_conversation2(conversation_id):
    try:
        return Conversation2.objects.get(pk=conversation_id)
    except Conversation2.DoesNotExist:
        return None


def get_message2(message_id):
    try:
        return Message2.objects.get(pk=message_id)
    except Message2.DoesNotExist:
        return None


def conversation2_exist(conversation_id=None, users=None, about=None):
    """
    Check whether a conversation with same id or both users and about exists
    """
    if conversation_id:
        return get_conversation2(conversation_id) or False
    elif users:
        assert isinstance(users, list)
        # remove duplicates if any
        users = list(set(users))

        if about:
            conversations = Conversation2.objects.with_attached_object(about)
        else:
            conversations = Conversation2.objects.filter(object_id=None)

        for user in users:
            conversations = conversations.filter(users=user)
        return conversations[0] if len(conversations) else False
    else:
        return False


def hide_conversation2_from_user(conversation, user):
    # todo: remove the user from conversation
    try:
        Conversation2Delete(user=user, conversation_id=conversation.id).save(True)
    except IntegrityError:
        pass


def hide_message2_from_user(message, user):
    try:
        Message2Delete(user=user, message_id=message.id, conversation_id=message.conversation.id).save(True)
    except IntegrityError:
        pass


def get_user_conversations(user, before=None, after=None, limit=25):
    """
    Return list of user Conversations
    :type user: User
    :type before: int unix
    :type after: int unix
    :type limit: int
    """
    conversations = user.conversations2.order_by('-modified_at')
    if before:
        conversations = conversations.filter(modified_at__lt=datetime.fromtimestamp(before))
    if after:
        conversations = conversations.filter(modified_at__gt=datetime.fromtimestamp(after))

    return conversations.select_related('last_message')[:limit]


def send_message2(conversation, user, to_users=None, about=None, text=None, attachments=None, request=None):
    assert conversation or to_users, "Either an existing conversation or a list of to_users should be provided to create a message."

    if to_users and isinstance(to_users, list):
        # conversation users include everyone in it
        to_users.append(user)

    if not conversation:
        conversation = conversation2_exist(users=to_users, about=about)

    if not conversation:
        if about:
            conversation = Conversation2(attached_object=about, type=CONVERSATION_TYPE_ABOUT_SHOUT)
        else:
            conversation = Conversation2(type=CONVERSATION_TYPE_CHAT)
        conversation.save()
        conversation.users = to_users

    message = Message2(conversation=conversation, user=user, text=text)
    message.save()

    conversation.last_message = message
    conversation.save()

    if not attachments:
        attachments = []

    for attachment in attachments:
        # todo: map the content types to models
        if MESSAGE_ATTACHMENT_TYPE_SHOUT.text in attachment:
            object_id = attachment[MESSAGE_ATTACHMENT_TYPE_SHOUT.text]['id']
            content_type = ContentType.objects.get_for_model(Trade)
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
            notifications_controller.notify_user_of_message2(to_user, message, request)

    return message


# backward compatibility functions
def message2_from_message(message):
    """
    Make a Message2 copy of message
    :type message: Message
    :return: Message2
    """

    # get or create Conversation2
    shout = message.Conversation.AboutPost
    ct = ContentType.objects.get_for_model(shout)
    conversation2, c2_created = Conversation2.objects.get_or_create(id=message.Conversation.id, content_type=ct, object_id=shout.id,
                                                                    type=CONVERSATION_TYPE_ABOUT_SHOUT)
    if c2_created:
        conversation2.users = [message.FromUser, message.ToUser]

    # get or create Message2
    message2, m2_created = Message2.objects.get_or_create(id=message.id, conversation=conversation2, user=message.FromUser)
    if m2_created:
        message2.text = message.text
        message2.save()

    conversation2.last_message = message2
    conversation2.save()


# todo: update to take date range and add it to messaging2
def read_conversation2(user, conversation):
    read_messages2_pks = [str(pk) for pk in user.read_messages2_set.filter(conversation_id=conversation.id).values_list('message__pk', flat=True)]
    other_messages2 = Message2.objects.filter(Q(conversation_id=conversation.id) & ~Q(pk__in=read_messages2_pks))
    for message2 in other_messages2:
        try:
            Message2Read(user=user, message=message2, conversation_id=conversation.id).save()
        except IntegrityError:
            pass
