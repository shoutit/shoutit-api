# -*- coding: utf-8 -*-
"""

"""
from __future__ import unicode_literals
from datetime import datetime

from django.db import models, IntegrityError
from django.conf import settings

from common.constants import ReportType, NotificationType, NOTIFICATION_TYPE_LISTEN, MessageAttachmentType, MESSAGE_ATTACHMENT_TYPE_SHOUT, \
    ConversationType, MESSAGE_ATTACHMENT_TYPE_LOCATION
from shoutit.models.base import UUIDModel, AttachedObjectMixin, APIModelMixin


AUTH_USER_MODEL = getattr(settings, 'AUTH_USER_MODEL')


class Conversation(UUIDModel):
    FromUser = models.ForeignKey(AUTH_USER_MODEL, related_name='+')
    ToUser = models.ForeignKey(AUTH_USER_MODEL, related_name='+')
    AboutPost = models.ForeignKey('shoutit.Trade', related_name='+')
    is_read = models.BooleanField(default=False)
    VisibleToRecivier = models.BooleanField(default=True)
    VisibleToSender = models.BooleanField(default=True)

    def __str__(self):
        return unicode(self.pk)

    @property
    def contributors(self):
        return [self.FromUser, self.ToUser]


class Message(UUIDModel):
    Conversation = models.ForeignKey('shoutit.Conversation', related_name='Messages')
    FromUser = models.ForeignKey(AUTH_USER_MODEL, related_name='received_messages')
    ToUser = models.ForeignKey(AUTH_USER_MODEL, related_name='sent_messages')
    text = models.TextField(null=True, blank=True)
    is_read = models.BooleanField(default=False)
    VisibleToRecivier = models.BooleanField(default=True)
    VisibleToSender = models.BooleanField(default=True)
    DateCreated = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        try:
            return unicode(self.pk) + ": " + "(" + unicode(self.FromUser) + " => " + unicode(self.ToUser) + "):" + (self.text[:50] if self.text else '')
        except AttributeError:
            return unicode(self.pk)

    @property
    def contributors(self):
        return [self.FromUser, self.ToUser]


class MessageAttachment(UUIDModel, AttachedObjectMixin):
    type = models.SmallIntegerField(choices=MessageAttachmentType.choices, blank=False)
    message = models.ForeignKey('shoutit.Message2', related_name='attachments')
    conversation = models.ForeignKey('shoutit.Conversation2', related_name='messages_attachments')

    def __str__(self):
        return self.pk + " for message: " + self.message.pk

    def type_name(self):
        return MessageAttachmentType.values[self.type]

    @property
    def shout(self):
        if self.type == MESSAGE_ATTACHMENT_TYPE_SHOUT:
            return self.attached_object
        else:
            return None

    @property
    def location(self):
        if self.type == MESSAGE_ATTACHMENT_TYPE_LOCATION:
            return self.attached_object
        else:
            return None


class Notification(UUIDModel, AttachedObjectMixin):
    ToUser = models.ForeignKey(AUTH_USER_MODEL, related_name='notifications')
    FromUser = models.ForeignKey(AUTH_USER_MODEL, related_name='+', null=True, blank=True, default=None)
    is_read = models.BooleanField(default=False)
    type = models.IntegerField(default=NOTIFICATION_TYPE_LISTEN.value, choices=NotificationType.choices)
    DateCreated = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.pk + ": " + self.text

    @property
    def text(self):
        return NotificationType.values[self.type]

    def MarkAsRead(self):
        self.is_read = True
        self.save()


class Report(UUIDModel, AttachedObjectMixin):
    user = models.ForeignKey(AUTH_USER_MODEL, related_name='Reports')
    text = models.TextField(default='', blank=True, max_length=300)
    type = models.IntegerField(default=0)
    IsSolved = models.BooleanField(default=False)
    is_disabled = models.BooleanField(default=False)
    DateCreated = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return "From user:%s about: %s:%s" % (self.user.pk, self.type(), self.attached_object.pk)

    @property
    def type(self):
        return ReportType.values[self.type]


########## M2 ###########
class Conversation2(UUIDModel, AttachedObjectMixin, APIModelMixin):
    """
    Conversation2 will introduce group chat where a conversation can have many users, each will contribute by creating Message2
    the attached_object is the topic of the conversation and it is allowed not to have a topic.
    """
    type = models.SmallIntegerField(choices=ConversationType.choices, blank=False)
    users = models.ManyToManyField(AUTH_USER_MODEL, related_name='conversations2')
    deleted_by = models.ManyToManyField(AUTH_USER_MODEL, through='shoutit.Conversation2Delete', related_name='deleted_conversations2')
    last_message = models.OneToOneField('shoutit.Message2', related_name='+', null=True, blank=True)

    def __str__(self):
        return "%s at:%s" % (self.pk, self.modified_at_unix)

    def get_messages(self, before=None, after=None, limit=25):
        messages = self.messages2.order_by('-created_at')
        if before:
            messages = messages.filter(created_at__lt=datetime.fromtimestamp(before))
        if after:
            messages = messages.filter(created_at__gt=datetime.fromtimestamp(after))
        return messages[:limit][::-1]

    def get_messages_qs(self, ):
        return self.messages2.order_by('-created_at')

    def get_messages_qs2(self, ):
        return self.messages2.all()

    @property
    def about(self):
        return self.attached_object

    @property
    def type_name(self):
        return ConversationType.values[self.type]

    @property
    def messages_count(self):
        return self.messages2.count()

    def unread_messages_count(self, user):
        return self.messages_count - user.read_messages2.filter(conversation=self).count()

    def mark_as_deleted(self, user):
        # 1 - record the deletion
        try:
            Conversation2Delete(user=user, conversation_id=self.id).save(True)
        except IntegrityError:
            pass

        # 2 - remove the user from the list of users
        if user in self.contributors:
            self.users.remove(user)

        # 3 - send a system message saying the user has left the conversation
        text = "{} has left the conversation".format(user.name)
        message = Message2(user=None, text=text, conversation=self)
        message.save()

        from shoutit.controllers import notifications_controller
        for to_user in self.contributors:
            notifications_controller.notify_user_of_message2(to_user, message)

    def mark_as_read(self, user):
        # todo: find more efficient way
        for message in self.messages2.all():
            try:
                Message2Read(user=user, message_id=message.id, conversation_id=message.conversation.id).save(True)
            except IntegrityError:
                pass

    def mark_as_unread(self, user):
        try:
            Message2Read.objects.get(user=user, message_id=self.last_message.id, conversation_id=self.id).delete()
        except Message2Read.DoesNotExist:
            pass

    @property
    def messages_attachments(self):
        return MessageAttachment.objects.filter(conversation_id=self.id)

    @property
    def contributors(self):
        return self.users.all()


class Conversation2Delete(UUIDModel):
    """
    Conversation2Delete is to record a user deleting a Conversation2
    """
    user = models.ForeignKey(AUTH_USER_MODEL, related_name='deleted_conversations2_set')
    conversation = models.ForeignKey('shoutit.Conversation2', related_name='deleted_set')

    class Meta(UUIDModel.Meta):
        # so the user can mark the conversation as 'deleted' only once
        unique_together = ('user', 'conversation')


class Message2(UUIDModel):
    """
    Message2 is a message from user into a Conversation2
    """
    user = models.ForeignKey(AUTH_USER_MODEL, related_name='+', null=True, blank=True, default=None)
    conversation = models.ForeignKey('shoutit.Conversation2', related_name='messages2')
    read_by = models.ManyToManyField(AUTH_USER_MODEL, through='shoutit.Message2Read', related_name='read_messages2')
    deleted_by = models.ManyToManyField(AUTH_USER_MODEL, through='shoutit.Message2Delete', related_name='deleted_messages2')
    text = models.CharField(null=True, blank=True, max_length=2000,
                            help_text="The text body of this message, could be None if the message has attachments")

    def __str__(self):
        return "%s c at:%s" % (self.text[:30] + '...' if self.text else '<attachment>', self.created_at_unix)

    @property
    def attachments(self):
        return MessageAttachment.objects.filter(message_id=self.id)

    @property
    def contributors(self):
        return self.conversation.contributors


class Message2Read(UUIDModel):
    """
    Message2Read is to record a user reading a Message2
    """
    user = models.ForeignKey(AUTH_USER_MODEL, related_name='read_messages2_set')
    message = models.ForeignKey('shoutit.Message2', related_name='read_set')
    conversation = models.ForeignKey('shoutit.Conversation2', related_name='messages2_read_set')

    class Meta(UUIDModel.Meta):
        # user can mark the message as 'read' only once
        unique_together = ('user', 'message', 'conversation')


class Message2Delete(UUIDModel):
    """
    Message2Read is to record a user deleting a Message2
    """
    user = models.ForeignKey(AUTH_USER_MODEL, related_name='deleted_messages2_set')
    message = models.ForeignKey(Message2, related_name='deleted_set')
    conversation = models.ForeignKey(Conversation2, related_name='messages2_deleted_set')

    class Meta(UUIDModel.Meta):
        # user can mark the message as 'deleted' only once
        unique_together = ('user', 'message', 'conversation')

