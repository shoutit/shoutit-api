# -*- coding: utf-8 -*-
"""

"""
from __future__ import unicode_literals
from datetime import datetime

from django.db import models, IntegrityError
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

from common.constants import (
    ReportType, NotificationType, NOTIFICATION_TYPE_LISTEN, MessageAttachmentType,
    MESSAGE_ATTACHMENT_TYPE_SHOUT, ConversationType, MESSAGE_ATTACHMENT_TYPE_LOCATION,
    REPORT_TYPE_GENERAL, CONVERSATION_TYPE_ABOUT_SHOUT)
from shoutit.models.base import UUIDModel, AttachedObjectMixin, APIModelMixin
from shoutit.utils import track

AUTH_USER_MODEL = getattr(settings, 'AUTH_USER_MODEL')


class Conversation(UUIDModel, AttachedObjectMixin, APIModelMixin):
    """
    Conversation will introduce group chat where a conversation can have many users, each will contribute by creating Message
    the attached_object is the topic of the conversation and it is allowed not to have a topic.
    """
    type = models.SmallIntegerField(choices=ConversationType.choices, blank=False)
    users = models.ManyToManyField(AUTH_USER_MODEL, related_name='conversations2')
    deleted_by = models.ManyToManyField(AUTH_USER_MODEL, through='shoutit.ConversationDelete',
                                        related_name='deleted_conversations2')
    last_message = models.OneToOneField('shoutit.Message', related_name='+', null=True, blank=True)

    def __unicode__(self):
        return "%s at:%s" % (self.pk, self.modified_at_unix)

    def get_messages(self, before=None, after=None, limit=25):
        messages = self.messages.order_by('-created_at')
        if before:
            messages = messages.filter(created_at__lt=datetime.fromtimestamp(before))
        if after:
            messages = messages.filter(created_at__gt=datetime.fromtimestamp(after))
        return messages[:limit][::-1]

    def get_messages_qs(self, ):
        return self.messages.order_by('-created_at')

    def get_messages_qs2(self, ):
        return self.messages.all()

    @property
    def about(self):
        return self.attached_object

    @property
    def type_name(self):
        return ConversationType.values[self.type]

    @property
    def messages_count(self):
        return self.messages.count()

    def unread_messages_count(self, user):
        return self.messages_count - user.read_messages.filter(conversation=self).count()

    def mark_as_deleted(self, user):
        # 1 - record the deletion
        try:
            ConversationDelete.objects.create(user=user, conversation_id=self.id)
        except IntegrityError:
            pass

        # 2 - remove the user from the list of users
        if user in self.contributors:
            self.users.remove(user)

        # 3 - create a system message saying the user has left the conversation
        text = "{} has left the conversation".format(user.name)
        Message.objects.create(user=None, text=text, conversation=self)

    def mark_as_read(self, user):
        # todo: find more efficient way
        for message in self.messages.all():
            try:
                MessageRead.objects.create(user=user, message_id=message.id,
                                           conversation_id=message.conversation.id)
            except IntegrityError:
                pass

    def mark_as_unread(self, user):
        try:
            MessageRead.objects.get(user=user, message_id=self.last_message.id,
                                    conversation_id=self.id).delete()
        except MessageRead.DoesNotExist:
            pass

    @property
    def messages_attachments(self):
        return MessageAttachment.objects.filter(conversation_id=self.id)

    @property
    def contributors(self):
        return self.users.all()

    @property
    def track_properties(self):
        properties = {
            'type': self.type_name
        }
        if self.about and self.type == CONVERSATION_TYPE_ABOUT_SHOUT and self.about.is_sss:
            properties.update({'about_sss': True})
        return properties


@receiver(post_save, sender=Conversation)
def post_save_conversation(sender, instance=None, created=False, **kwargs):
    if created:
        track(getattr(instance, 'creator_id'), 'new_conversation', instance.track_properties)


class ConversationDelete(UUIDModel):
    """
    ConversationDelete is to record a user deleting a Conversation
    """
    user = models.ForeignKey(AUTH_USER_MODEL, related_name='deleted_conversations2_set')
    conversation = models.ForeignKey('shoutit.Conversation', related_name='deleted_set')

    class Meta(UUIDModel.Meta):
        # so the user can mark the conversation as 'deleted' only once
        unique_together = ('user', 'conversation')


class Message(UUIDModel):
    """
    Message is a message from user into a Conversation
    """
    user = models.ForeignKey(AUTH_USER_MODEL, related_name='+', null=True, blank=True, default=None)
    conversation = models.ForeignKey('shoutit.Conversation', related_name='messages')
    read_by = models.ManyToManyField(AUTH_USER_MODEL, through='shoutit.MessageRead',
                                     related_name='read_messages')
    deleted_by = models.ManyToManyField(AUTH_USER_MODEL, through='shoutit.MessageDelete',
                                        related_name='deleted_messages')
    text = models.CharField(null=True, blank=True, max_length=2000,
                            help_text="The text body of this message, could be None if the message has attachments")

    def __unicode__(self):
        return "%s  at:%s" % (self.summary, self.created_at_unix)

    @property
    def summary(self):
        return (getattr(self, 'text') or '<attachment>')[:30]

    @property
    def attachments(self):
        return MessageAttachment.objects.filter(message_id=self.id)

    @property
    def contributors(self):
        return self.conversation.contributors

    def is_read(self, user):
        return MessageRead.objects.filter(user=user, message=self,
                                          conversation=self.conversation).exists()


@receiver(post_save, sender=Message)
def post_save_message(sender, instance=None, created=False, **kwargs):
    if created:
        # update the conversation
        conversation = instance.conversation
        conversation.last_message = instance
        conversation.save()
        # read it by its owner if exists (not by system)
        if instance.user:
            MessageRead.objects.create(user=instance.user, message=instance, conversation=conversation)

        if getattr(instance, 'send_notification', True):
            from shoutit.controllers import notifications_controller
            for to_user in conversation.contributors:
                if instance.user and instance.user != to_user:
                    notifications_controller.notify_user_of_message(to_user, instance)


class MessageRead(UUIDModel):
    """
    MessageRead is to record a user reading a Message
    """
    user = models.ForeignKey(AUTH_USER_MODEL, related_name='read_messages_set')
    message = models.ForeignKey('shoutit.Message', related_name='read_set')
    conversation = models.ForeignKey('shoutit.Conversation', related_name='messages_read_set')

    class Meta(UUIDModel.Meta):
        # user can mark the message as 'read' only once
        unique_together = ('user', 'message', 'conversation')


class MessageDelete(UUIDModel):
    """
    MessageDelete is to record a user deleting a Message
    """
    user = models.ForeignKey(AUTH_USER_MODEL, related_name='deleted_messages_set')
    message = models.ForeignKey(Message, related_name='deleted_set')
    conversation = models.ForeignKey(Conversation, related_name='messages_deleted_set')

    class Meta(UUIDModel.Meta):
        # user can mark the message as 'deleted' only once
        unique_together = ('user', 'message', 'conversation')


class MessageAttachment(UUIDModel, AttachedObjectMixin):
    type = models.SmallIntegerField(choices=MessageAttachmentType.choices, blank=False)
    message = models.ForeignKey('shoutit.Message', related_name='attachments')
    conversation = models.ForeignKey('shoutit.Conversation', related_name='messages_attachments')

    def __unicode__(self):
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
    FromUser = models.ForeignKey(AUTH_USER_MODEL, related_name='+', null=True, blank=True,
                                 default=None)
    type = models.IntegerField(default=NOTIFICATION_TYPE_LISTEN.value,
                               choices=NotificationType.choices)
    is_read = models.BooleanField(default=False)

    def __unicode__(self):
        return self.pk + ": " + self.type_name

    @property
    def type_name(self):
        return NotificationType.values[self.type]

    def mark_as_read(self):
        self.is_read = True
        self.save()


class Report(UUIDModel, AttachedObjectMixin):
    user = models.ForeignKey(AUTH_USER_MODEL, related_name='reports')
    text = models.TextField(null=True, blank=True, max_length=300)
    type = models.IntegerField(default=REPORT_TYPE_GENERAL.value, choices=ReportType.choices)
    is_solved = models.BooleanField(default=False)
    is_disabled = models.BooleanField(default=False)

    def __unicode__(self):
        return "From user:%s about: %s:%s" % (self.user.pk, self.type_name, self.attached_object.pk)

    @property
    def type_name(self):
        return ReportType.values[self.type]
