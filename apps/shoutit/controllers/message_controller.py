from datetime import datetime
from django.contrib.contenttypes.models import ContentType
from django.db import IntegrityError
from django.db.models.aggregates import Max
from django.db.models.query_utils import Q

from apps.shoutit.models import Conversation, Message, MessageAttachment, Tag, StoredImage, Trade, Conversation2, Message2, \
    Message2Attachment2, Conversation2Delete, Message2Delete, Message2Read
from apps.shoutit.controllers import email_controller, notifications_controller, shout_controller


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


def send_message(from_user, to_user, about, text=None, attachments=None, conversation=None):

    if not conversation:
        conversation = conversation_exist(user1=from_user, user2=to_user, about=about)

    if not conversation:
        conversation = Conversation(FromUser=from_user, ToUser=to_user, AboutPost=about)

    # todo: fix visibility to sender receiver!?
    conversation.IsRead = False
    conversation.VisibleToSender = True
    conversation.VisibleToRecivier = True
    conversation.save()

    message = Message(Conversation=conversation, FromUser=from_user, ToUser=to_user, Text=text if text else None)
    message.save()

    if not attachments:
        attachments = []

    for attachment in attachments:
        object_id = attachment['object_id']
        content_type = ContentType.objects.get_for_model(Trade)  # todo: map the content types to models
        MessageAttachment(message=message, content_type=content_type, object_id=object_id).save()

    notifications_controller.notify_user_of_message(to_user, message)
    email_controller.send_message_email(message)

    return message


# todo: simplify this SHIT!
def getFullConversationDetails(conversations, user):
    result_conversations = []
    conversation_ids = [conversation.pk for conversation in conversations]
    conversations_messages = Message.objects.filter(Q(Conversation__pk__in=conversation_ids) & (
    (Q(FromUser=user) & Q(VisibleToSender=True)) | (Q(ToUser=user) & Q(VisibleToRecivier=True)))).select_related(
        'Conversation', 'ToUser', 'ToUser__Profile', 'FromUser', 'FromUser__Profile')
    shout_pks = [conversation.AboutPost.pk for conversation in conversations]

    if shout_pks:
        tags = Tag.objects.select_related('Creator').prefetch_related('Shouts')
        tags = tags.extra(where=['shout_id IN (%s)' % ','.join(["'%s'" % str(shout_pk) for shout_pk in shout_pks])])
        tags_with_shout_id = list(tags.values('pk', 'Name', 'Creator', 'image', 'DateCreated', 'Definition', 'Shouts__pk'))

    else:
        tags_with_shout_id = []

    images = StoredImage.objects.filter(Item__pk__in=[conversation.AboutPost.Item.pk for conversation in conversations]).order_by('image')

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
        conversation.AboutPost.set_images([image for image in images if image.Item.pk == conversation.AboutPost.Item.pk])
        conversation.AboutPost.set_tags([tag for tag in tags_with_shout_id if str(tag['Shouts__pk']) == conversation.AboutPost.pk])
        last_message = list(conversation.messages)[-1]
        conversation.Text = last_message.Text[0:256] if last_message.Text else "attachment"
        conversation.DateCreated = list(conversation.messages)[-1].DateCreated
        conversation.With = conversation.FromUser if conversation.FromUser != user else conversation.ToUser
        conversation.IsRead = False if [1 if message.ToUser == user and not message.IsRead else 0 for message in
                                        conversation.messages].count(1) else True
        result_conversations.append(conversation)

    Conversation.objects.filter(pk__in=empty_conversations_from).update(VisibleToSender=False)
    Conversation.objects.filter(pk__in=empty_conversations_to).update(VisibleToRecivier=False)
    return result_conversations


def ReadConversations(user, start_index=None, end_index=None):
    conversations = Conversation.objects.filter(
        ((Q(FromUser=user) & Q(VisibleToSender=True)) | (Q(ToUser=user) & Q(VisibleToRecivier=True)))
    ).select_related('FromUser',
                     'FromUser__Profile',
                     'ToUser',
                     'ToUser__Profile',
                     'AboutPost',
                     'AboutPost__Item',
                     'AboutPost__Item__Currency',
                     'AboutPost__Item__Images',
                     'AboutPost__shout',
                     'AboutPost__OwnerUser',
                     'AboutPost__OwnerUser__Profile').annotate(max_date=Max('Messages__DateCreated')).order_by(
        '-max_date')[start_index:end_index]
    return getFullConversationDetails(conversations, user)


def ReadConversation(user, conversation_id):
    conversation = Conversation.objects.get(pk=conversation_id)
    Message.objects.filter(Q(Conversation=conversation) & (Q(FromUser=user) | Q(ToUser=user))).update(IsRead=True)
    messages = Message.objects.filter(
        Q(Conversation=conversation) & ((Q(FromUser=user) & Q(VisibleToSender=True)) | (Q(ToUser=user) & Q(VisibleToRecivier=True)))
    ).order_by('DateCreated')
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
        conversations = getFullConversationDetails([conversation], user)
        conversation = conversations[0] if len(conversations) else None
        return conversation


def get_shout_conversations(shout_id, user):
    # todo: simplify
    shout = shout_controller.get_post(shout_id, True, True)
    if user.is_authenticated() and user.pk == shout.OwnerUser.pk:
        conversations = Conversation.objects.filter(AboutPost=shout, ToUser=user, VisibleToRecivier=True).annotate(
            max_date=Max('Messages__DateCreated')).select_related('ToUser', 'ToUser__Profile', 'FromUser',
                                                                  'FromUser__Profile', 'AboutPost', 'AboutPost__Item',
                                                                  'AboutPost__Item__Currency', 'AboutPost__shout',
                                                                  'AboutPost__shout__Tags',
                                                                  'AboutPost__shout__Images').order_by('-max_date')
        conversations = getFullConversationDetails(conversations, user)
    elif user.is_authenticated():
        conversations = Conversation.objects.filter(AboutPost=shout, FromUser=user, VisibleToSender=True).annotate(
            max_date=Max('Messages__DateCreated')).select_related('ToUser', 'ToUser__Profile', 'FromUser',
                                                                  'FromUser__Profile', 'AboutPost', 'AboutPost__Item',
                                                                  'AboutPost__Item__Currency', 'AboutPost__shout',
                                                                  'AboutPost__shout__Tags',
                                                                  'AboutPost__shout__Images').order_by('-max_date')
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


def GetMessage(pk):
    message = Message.objects.get(pk=pk)
    if message:
        return message
    else:
        return None


def hide_conversation_from_user(conversation, user):
    if user == conversation.FromUser:
        conversation.VisibleToSender = False
    else:
        conversation.VisibleToRecivier = False
    conversation.save()


def ConversationsCount(user):
    return Conversation.objects.filter(
        (Q(FromUser=user) & Q(VisibleToSender=True)) | (Q(ToUser=user) & Q(VisibleToRecivier=True))).count()


def UnReadConversationsCount(user):
    return Conversation.objects.filter(Q(Messages__ToUser=user) & Q(Messages__IsRead=False) & (
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
    if conversation_id:
        return get_conversation2(conversation_id) or False
    elif users:
        conversations = Conversation2.objects.with_attached_object(about) if about else Conversation2.objects.filter(object_id=None)
        for user in users:
            conversations = conversations.filter(users=user)
        return conversations[0] if len(conversations) else False
    else:
        return False


def hide_conversation2_from_user(conversation, user):
    try:
        conversation_delete = Conversation2Delete.objects.get(user=user, conversation=conversation)
    except Conversation2Delete.DoesNotExist:
        conversation_delete = Conversation2Delete(user=user, conversation=conversation)

    conversation_delete.save()


def hide_message2_from_user(conversation, message, user):
    try:
        Message2Delete(user=user, message=message, conversation=conversation).save()
    except IntegrityError:
        pass


def mark_message2_as_read(conversation, message, user):
    try:
        read = Message2Read(user=user, message=message, conversation=conversation)
        read.save()
    except IntegrityError:
        pass


def mark_message2_as_unread(conversation, message, user):
    try:
        read = Message2Read.objects.filter(user=user, message=message, conversation=conversation)
        read.delete()
    except Message2Read.DoesNotExist:
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


def send_message2(conversation, user, to_users=None, about=None, text=None, attachments=None):
    if not (conversation or to_users):
        raise Exception('Either an existing conversation or a list of to_users should be provided to create a message.')

    if not conversation:
        to_users.append(user)
        conversation = conversation2_exist(users=to_users, about=about)

    if not conversation:
        conversation = Conversation2(attached_object=about) if about else Conversation2()
        conversation.save()
        conversation.users = to_users

    message = Message2(conversation=conversation, user=user, message=text)
    message.save()

    conversation.last_message = message
    conversation.save()

    if not attachments:
        attachments = []

    for attachment in attachments:
        object_id = attachment['object_id']
        content_type = ContentType.objects.get_for_model(Trade)  # todo: map the content types to models
        Message2Attachment2(message=message, content_type=content_type, object_id=object_id).save()

    # notifications_controller.notify_user_of_message(to_user, message)
    # email_controller.send_message_email(message)

    return message


