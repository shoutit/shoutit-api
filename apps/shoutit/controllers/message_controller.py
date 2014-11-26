from django.contrib.contenttypes.models import ContentType
from django.db.models.aggregates import Max
from django.db.models.query_utils import Q
from django.core.exceptions import ObjectDoesNotExist

from apps.shoutit.models import Conversation, Message, MessageAttachment, Tag, StoredImage, Trade
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
    except ObjectDoesNotExist:
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
        object_pk = attachment['object_id']
        content_type = ContentType.objects.get_for_model(Trade)  # todo: map the content types to models
        MessageAttachment(message=message, content_type=content_type, object_pk=object_pk).save()

    # todo: push notification test
    notifications_controller.NotifyUserOfMessage(to_user, message)
    email_controller.SendMessageEmail(message)

    return message


# todo: simplify this SHIT!
def getFullConversationDetails(conversations, user):
    result_conversations = []
    conversation_ids = [conversation.pk for conversation in conversations]
    conversations_messages = Message.objects.filter(Q(Conversation__pk__in=conversation_ids) & (
    (Q(FromUser=user) & Q(VisibleToSender=True)) | (Q(ToUser=user) & Q(VisibleToRecivier=True)))).select_related(
        'Conversation', 'ToUser', 'ToUser__Profile', 'FromUser', 'FromUser__Profile')
    shouts_pks = [conversation.AboutPost.pk for conversation in conversations]

    if shouts_pks:
        tags = Tag.objects.select_related('Creator').prefetch_related('Shouts')
        tags = tags.extra(where=['shout_id IN (%s)' % ','.join(["'%s'" % str(shout_pk) for shout_pk in shouts_pks])])
        tags_with_shout_id = list(tags.values('pk', 'Name', 'Creator', 'Image', 'DateCreated', 'Definition', 'Shouts__pk'))

    else:
        tags_with_shout_id = []

    images = StoredImage.objects.filter(Item__pk__in=[conversation.AboutPost.Item.pk for conversation in conversations]).order_by('Image')

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
        conversation.AboutPost.SetImages([image for image in images if image.Item.pk == conversation.AboutPost.Item.pk])
        conversation.AboutPost.SetTags([tag for tag in tags_with_shout_id if tag['Shouts__pk'] == conversation.AboutPost.pk])
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
    except ObjectDoesNotExist:
        conversation = None

    if user is None:
        if conversation:
            return conversation
        else:
            return None
    else:
        conversations = getFullConversationDetails([conversation], user)
        conversation = conversations[0] if len(conversations) else None
        return conversation


def get_shout_conversations(shout_id, user):
    #todo: simplify
    shout = shout_controller.GetPost(shout_id, True, True)
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


def DeleteMessage(user, pk):
    message = Message.objects.get(pk=pk)
    if user.username == message.FromUser.username:
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


def DeleteConversation(user, pk):
    conversation = Conversation.objects.get(pk=pk)
    if user.username == conversation.FromUser.username:
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
