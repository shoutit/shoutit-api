from datetime import datetime

from django.db import models
from django.conf import settings

from common.constants import ReportType, NotificationType, NOTIFICATION_TYPE_LISTEN
from shoutit.models.base import UUIDModel, AttachedObjectMixin


AUTH_USER_MODEL = getattr(settings, 'AUTH_USER_MODEL')


class Conversation(UUIDModel):
    FromUser = models.ForeignKey(AUTH_USER_MODEL, related_name='+')
    ToUser = models.ForeignKey(AUTH_USER_MODEL, related_name='+')
    AboutPost = models.ForeignKey('shoutit.Trade', related_name='+')
    IsRead = models.BooleanField(default=False)
    VisibleToRecivier = models.BooleanField(default=True)
    VisibleToSender = models.BooleanField(default=True)

    def __unicode__(self):
        return unicode(self.pk)


class Message(UUIDModel):
    Conversation = models.ForeignKey('shoutit.Conversation', related_name='Messages')
    FromUser = models.ForeignKey(AUTH_USER_MODEL, related_name='received_messages')
    ToUser = models.ForeignKey(AUTH_USER_MODEL, related_name='sent_messages')
    Text = models.TextField(null=True, blank=True)
    IsRead = models.BooleanField(default=False)
    VisibleToRecivier = models.BooleanField(default=True)
    VisibleToSender = models.BooleanField(default=True)
    DateCreated = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        try:
            return unicode(self.pk) + ": " + "(" + unicode(self.FromUser) + " => " + unicode(self.ToUser) + "):" + (self.Text[:50] if self.Text else '')
        except AttributeError:
            return unicode(self.pk)


class MessageAttachment(UUIDModel, AttachedObjectMixin):
    message = models.ForeignKey('shoutit.Message', related_name='attachments')
    conversation = models.ForeignKey('shoutit.Conversation', related_name='messages_attachments')

    def __unicode__(self):
        return self.pk + " for message: " + self.message.pk


class Notification(UUIDModel, AttachedObjectMixin):
    ToUser = models.ForeignKey(AUTH_USER_MODEL, related_name='Notifications')
    FromUser = models.ForeignKey(AUTH_USER_MODEL, related_name='+', null=True, blank=True, default=None)
    IsRead = models.BooleanField(default=False)
    Type = models.IntegerField(default=NOTIFICATION_TYPE_LISTEN.value, choices=NotificationType.choices)
    DateCreated = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return self.pk + ": " + self.Text

    @property
    def Text(self):
        return NotificationType.values[self.Type]

    def MarkAsRead(self):
        self.IsRead = True
        self.save()


class Report(UUIDModel, AttachedObjectMixin):
    user = models.ForeignKey(AUTH_USER_MODEL, related_name='Reports')
    Text = models.TextField(default='', blank=True, max_length=300)
    Type = models.IntegerField(default=0)
    IsSolved = models.BooleanField(default=False)
    IsDisabled = models.BooleanField(default=False)
    DateCreated = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return "From user:%s about: %s:%s" % (self.user.pk, self.Type(), self.attached_object.pk)

    @property
    def Type(self):
        return ReportType.values[self.Type]


########## M2 ###########
class Conversation2(UUIDModel, AttachedObjectMixin):
    """
    Conversation2 will introduce group chat where a conversation can have many users, each will contribute by creating Message2
    the attached_object is the topic of the conversation and it is allowed not to have a topic.
    """
    users = models.ManyToManyField(AUTH_USER_MODEL, related_name='conversations2')
    deleted_by = models.ManyToManyField(AUTH_USER_MODEL, through='shoutit.Conversation2Delete', related_name='deleted_conversations2')
    last_message = models.OneToOneField('shoutit.Message2', related_name='+', null=True, blank=True)

    def __unicode__(self):
        return "%s at:%s" % (self.pk, self.modified_at_unix)

    def get_messages(self, before=None, after=None, limit=25):
        messages = self.messages2.order_by('-created_at')
        if before:
            messages = messages.filter(created_at__lt=datetime.fromtimestamp(before))
        if after:
            messages = messages.filter(created_at__gt=datetime.fromtimestamp(after))
        return messages[:limit][::-1]

    @property
    def messages_attachments(self):
        return MessageAttachment.objects.filter(conversation_id=self.id)


class Conversation2Delete(UUIDModel):
    """
    Conversation2Delete is to record a user deleting a Conversation2
    """
    user = models.ForeignKey(AUTH_USER_MODEL, related_name='deleted_conversations2_set')
    conversation = models.ForeignKey('shoutit.Conversation2', related_name='deleted_set')

    class Meta(UUIDModel.Meta):
        unique_together = ('user', 'conversation')  # so the user can mark the conversation as 'deleted' only once


class Message2(UUIDModel):
    """
    Message2 is a message from user into a Conversation2
    """
    user = models.ForeignKey(AUTH_USER_MODEL, related_name='+')
    conversation = models.ForeignKey('shoutit.Conversation2', related_name='messages2')
    read_by = models.ManyToManyField(AUTH_USER_MODEL, through='shoutit.Message2Read', related_name='read_messages2')
    deleted_by = models.ManyToManyField(AUTH_USER_MODEL, through='shoutit.Message2Delete', related_name='deleted_messages2')
    message = models.CharField(null=True, blank=True, max_length=2000)

    def __unicode__(self):
        return "%s c at:%s" % (self.message[:30] + '...' if self.message else '<attachment>', self.created_at_unix)

    @property
    def attachments(self):
        return MessageAttachment.objects.filter(message_id=self.id)


class Message2Read(UUIDModel):
    """
    Message2Read is to record a user reading a Message2
    """
    user = models.ForeignKey(AUTH_USER_MODEL, related_name='read_messages2_set')
    message = models.ForeignKey('shoutit.Message2', related_name='read_set')
    conversation = models.ForeignKey('shoutit.Conversation2', related_name='messages2_read_set')

    class Meta(UUIDModel.Meta):
        unique_together = ('user', 'message', 'conversation')  # so the user can mark the message as 'read' only once


class Message2Delete(UUIDModel):
    """
    Message2Read is to record a user deleting a Message2
    """
    user = models.ForeignKey(AUTH_USER_MODEL, related_name='deleted_messages2_set')
    message = models.ForeignKey(Message2, related_name='deleted_set')
    conversation = models.ForeignKey(Conversation2, related_name='messages2_deleted_set')

    class Meta(UUIDModel.Meta):
        unique_together = ('user', 'message', 'conversation')  # so the user can mark the message as 'deleted' only once