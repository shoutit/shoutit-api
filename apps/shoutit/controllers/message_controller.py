from django.db.models.aggregates import Max
from django.db.models.query_utils import Q

def ConversationExist(user1, user2, trade):
    conversation = Conversation.objects.filter(
        Q(AboutPost = trade)
        &	((Q(FromUser = user1) & Q(ToUser = user2))	|	(Q(FromUser = user2) & Q(ToUser = user1)))
    )
    if (conversation is not None) and (len (conversation)):
        return conversation[0]
    else:
        return None

def SendMessage(fromUser, toUser, trade, text, conversation_id=0):
    if not conversation_id:
        conversation = ConversationExist(fromUser, toUser, trade)
    else:
        conversation = GetConversation(conversation_id, fromUser)
        if fromUser.pk == conversation.ToUser_id:
            toUser = conversation.FromUser

    if conversation is None:
        conversation = Conversation(FromUser = fromUser, ToUser = toUser, AboutPost = trade)
    else:
        conversation.IsRead = False

    conversation.VisibleToSender = True
    conversation.VisibleToRecivier = True
    conversation.save()
    msg = Message(Conversation = conversation, FromUser = fromUser, ToUser = toUser, Text = text)
    msg.save()
    apps.shoutit.controllers.notifications_controller.NotifyUserOfMessage(toUser, msg)
    apps.shoutit.controllers.email_controller.SendMessageEmail(msg)
    return msg


def getFullConversationDetails(conversations, user):
    result_conversations = []
    conversation_ids = [conversation.id for conversation in conversations]
    conversations_messages = Message.objects.filter(Q(Conversation__id__in = conversation_ids) & ((Q(FromUser = user) & Q(VisibleToSender = True)) | (Q(ToUser=user) & Q(VisibleToRecivier = True)))).select_related('Conversation', 'ToUser','ToUser__Profile','FromUser','FromUser__Profile')
    shouts_ids = [conversation.AboutPost.pk for conversation in conversations]
    if shouts_ids:
        tags = Tag.objects.select_related('Creator').prefetch_related('Shouts')
        tags = tags.extra(where=['shout_id IN (%s)' % ','.join([str(pk) for pk in shouts_ids])])
        tags_with_shout_id = list(tags.values('id', 'Name', 'Creator', 'Image', 'DateCreated', 'Definition', 'Shouts__id'))

        #tags = Tag.objects.extra(select={'shout_id' : '"%s"."%s"' % (Shout.Tags.field.m2m_db_table(), Shout.Tags.field.m2m_column_name())})
        #tags.query.join((None, Tag._meta.db_table, None, None))
        #connection = (Tag._meta.db_table, Shout.Tags.field.m2m_db_table(), Tag._meta.pk.column, Shout.Tags.field.m2m_reverse_name())
        #tags.query.join(connection, promote=True)
        #tags = tags.extra(where=['shout_id IN (%s)' % ','.join([str(pk) for pk in shouts_ids])])
        #tags_with_shout_id = list(tags)
    else:
        tags_with_shout_id = []

    images = StoredImage.objects.filter(Item__pk__in = [conversation.AboutPost.Item.pk for conversation in conversations]).order_by('Image')

    empty_conversations_to = []
    empty_conversations_from = []
    for conversation in conversations:
        conversation.messages = [message for message in conversations_messages if message.Conversation_id == conversation.id]
        if not len(conversation.messages):
            if conversation.FromUser == user: empty_conversations_from.append(conversation.id)
            else: empty_conversations_to.append(conversation.id)
            continue
        conversation.AboutPost.SetImages([image for image in images if image.Item_id == conversation.AboutPost.Item_id])
        conversation.AboutPost.SetTags([tag for tag in tags_with_shout_id if tag['Shouts__id'] == conversation.AboutPost.pk])
        #conversation.AboutPost.SetTags([tag for tag in tags_with_shout_id if tag.shout_id == conversation.AboutPost.pk])
        conversation.Text = list(conversation.messages)[-1].Text[0:256]
        conversation.DateCreated = list(conversation.messages)[-1].DateCreated
        conversation.With = conversation.FromUser if conversation.FromUser != user else conversation.ToUser
        conversation.IsRead = False if [1 if message.ToUser == user and message.IsRead == False else 0 for message in conversation.messages].count(1) else True
        result_conversations.append(conversation)

    Conversation.objects.filter(pk__in = empty_conversations_from).update(VisibleToSender = False)
    Conversation.objects.filter(pk__in = empty_conversations_to).update(VisibleToRecivier = False)
    return result_conversations


def ReadConversations(user, start_index=None, end_index=None):

    conversations = Conversation.objects.filter(
        ((Q(FromUser = user) & Q(VisibleToSender = True)) | (Q(ToUser=user) & Q(VisibleToRecivier = True)))
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
        'AboutPost__OwnerUser__Profile').annotate(max_date=Max('Messages__DateCreated')).order_by('-max_date')[start_index:end_index]
    return getFullConversationDetails(conversations,user)

def ReadConversation(user, id):
    conversation = Conversation.objects.get(pk = id)
    Message.objects.filter(Q(Conversation = conversation) & (Q(FromUser = user)  | Q(ToUser=user) )).update(IsRead=True)
    messages = Message.objects.filter(Q(Conversation = conversation) & ((Q(FromUser = user) & Q(VisibleToSender = True)) | (Q(ToUser=user) & Q(VisibleToRecivier = True))) ).order_by('DateCreated')
    return messages

def GetConversation(id,user=None):
    conversation = Conversation.objects.get(pk = id)
    if user is None:
        if conversation:
            return conversation
        else:
            return None
    else:
        conversations = getFullConversationDetails([conversation],user)
        conversation = conversations[0] if len(conversations) else None
        return conversation

def GetShoutConversations(shout_id, user):
    shout = apps.shoutit.controllers.shout_controller.GetPost(shout_id, True, True)
    if user.is_authenticated() and user.pk == shout.OwnerUser.pk:
        conversations = Conversation.objects.filter(AboutPost = shout, ToUser = user, VisibleToRecivier = True).annotate(max_date=Max('Messages__DateCreated')).select_related('ToUser','ToUser__Profile','FromUser','FromUser__Profile','AboutPost','AboutPost__Item','AboutPost__Item__Currency','AboutPost__shout','AboutPost__shout__Tags','AboutPost__shout__Images').order_by('-max_date')
        conversations = getFullConversationDetails(conversations,user)
    elif user.is_authenticated():
        conversations = Conversation.objects.filter(AboutPost = shout, FromUser = user, VisibleToSender = True).annotate(max_date=Max('Messages__DateCreated')).select_related('ToUser','ToUser__Profile','FromUser','FromUser__Profile','AboutPost','AboutPost__Item','AboutPost__Item__Currency','AboutPost__shout','AboutPost__shout__Tags','AboutPost__shout__Images').order_by('-max_date')
        conversations = getFullConversationDetails(conversations,user)
    else:
        conversations = []

    return conversations

def DeleteMessage(user,id):
    message = Message.objects.get(pk=id)
    if user.username == message.FromUser.username:
        message.VisibleToSender = False

    else:
        message.VisibleToRecivier = False
    message.save()

def GetMessage(id):
    message = Message.objects.get(pk = id)
    if message:
        return message
    else:
        return None

def DeleteConversation(user,id):
    conversation = Conversation.objects.get(pk=id)
    if user.username == conversation.FromUser.username:
        conversation.VisibleToSender = False
    else:
        conversation.VisibleToRecivier = False
    conversation.save()

def ConversationsCount(user):
    return Conversation.objects.filter((Q(FromUser = user) & Q(VisibleToSender = True)) | (Q(ToUser=user) & Q(VisibleToRecivier = True))).count()

def UnReadConversationsCount(user):
    return Conversation.objects.filter(Q(Messages__ToUser = user) & Q(Messages__IsRead=False) & ((Q(FromUser = user) & Q(VisibleToSender = True)) | (Q(ToUser=user) & Q(VisibleToRecivier = True)))).values("id").distinct().count()

import apps.shoutit.controllers.email_controller
import apps.shoutit.controllers.notifications_controller
import apps.shoutit.controllers.shout_controller
from apps.shoutit.models import Conversation, Message, Tag, Shout, StoredImage