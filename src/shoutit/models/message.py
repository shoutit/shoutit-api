# -*- coding: utf-8 -*-
"""

"""
from __future__ import unicode_literals

from datetime import datetime

from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.contrib.contenttypes.fields import GenericRelation
from django.contrib.postgres.fields import ArrayField
from django.db import models, IntegrityError
from django.db.models.signals import post_save
from django.dispatch import receiver
from django_pgjson.fields import JsonField

from common.constants import (
    ReportType, NotificationType, NOTIFICATION_TYPE_LISTEN, MessageAttachmentType, MESSAGE_ATTACHMENT_TYPE_SHOUT,
    ConversationType, MESSAGE_ATTACHMENT_TYPE_LOCATION, REPORT_TYPE_GENERAL, CONVERSATION_TYPE_ABOUT_SHOUT,
    CONVERSATION_TYPE_PUBLIC_CHAT, NOTIFICATION_TYPE_MESSAGE, MESSAGE_ATTACHMENT_TYPE_MEDIA)
from common.utils import date_unix, utcfromtimestamp
from .action import Action
from .base import UUIDModel, AttachedObjectMixin, APIModelMixin, NamedLocationMixin
from ..utils import none_to_blank, track_new_message

AUTH_USER_MODEL = getattr(settings, 'AUTH_USER_MODEL')


class Conversation(UUIDModel, AttachedObjectMixin, APIModelMixin, NamedLocationMixin):
    """
    Conversation will introduce group chat where a conversation can have many users, each will contribute by creating Message
    the attached_object is the topic of the conversation and it is allowed not to have a topic.
    """
    type = models.SmallIntegerField(choices=ConversationType.choices, blank=False)
    users = models.ManyToManyField(AUTH_USER_MODEL, blank=True, related_name='conversations')
    creator = models.ForeignKey(AUTH_USER_MODEL, related_name='created_conversations', null=True, blank=True)
    subject = models.CharField(max_length=25, blank=True, default='')
    icon = models.URLField(blank=True, default='')
    admins = ArrayField(models.UUIDField(), default=list, blank=True)
    deleted_by = models.ManyToManyField(AUTH_USER_MODEL, through='shoutit.ConversationDelete',
                                        related_name='deleted_conversations')
    last_message = models.OneToOneField('shoutit.Message', related_name='+', null=True, blank=True)

    def __unicode__(self):
        return "%s at:%s" % (self.pk, self.modified_at_unix)

    def get_messages(self, before=None, after=None, limit=25):
        messages = self.messages.order_by('-created_at')
        if before:
            messages = messages.filter(created_at__lt=utcfromtimestamp(before))
        if after:
            messages = messages.filter(created_at__gt=utcfromtimestamp(after))
        return messages[:limit][::-1]

    def get_messages_qs(self, ):
        return self.messages.all()

    @property
    def about(self):
        return self.attached_object

    @property
    def messages_count(self):
        return self.messages.count()

    def unread_messages_count(self, user):
        if isinstance(user, AnonymousUser):
            return 0
        user_own_messages_count = user.messages.filter(conversation=self).count()
        user_read_messages_count = user.read_messages.filter(conversation=self).exclude(user=user).count()
        total_read_messages_count = user_own_messages_count + user_read_messages_count
        count = self.messages_count - total_read_messages_count
        return count

    def mark_as_deleted(self, user):
        # 0 - Mark all its messages as read
        self.mark_as_read(user)

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
        # Todo: track `conversation_delete` event?

    def mark_as_read(self, user):
        # Read all the notifications about this conversation
        notifications = Notification.objects.filter(is_read=False, to_user=user, type=NOTIFICATION_TYPE_MESSAGE,
                                                    message__conversation=self)
        notifications.update(is_read=True)

        # Trigger `stats_update` on Pusher
        from ..controllers import pusher_controller
        pusher_controller.trigger_stats_update(user, 'v3')

        # Read all the conversation's messages
        # Todo: Optimize!
        for message in self.messages.exclude(user=user):
            message.mark_as_read(user, trigger_stats_update=False)

    def mark_as_unread(self, user):
        try:
            MessageRead.objects.get(user=user, message_id=self.last_message.id, conversation_id=self.id).delete()
        except MessageRead.DoesNotExist:
            pass

    @property
    def messages_attachments(self):
        return MessageAttachment.objects.filter(conversation_id=self.id)

    @property
    def contributors(self):
        return self.users.all()

    def can_contribute(self, user):
        if self.type == CONVERSATION_TYPE_PUBLIC_CHAT:
            return True
        else:
            return user in self.contributors


@receiver(post_save, sender=Conversation)
def post_save_conversation(sender, instance=None, created=False, **kwargs):
    from ..controllers import pusher_controller

    if not created and getattr(instance, 'notify', True):
        # Trigger `conversation_update` event in the conversation channel
        pusher_controller.trigger_conversation_update(instance, 'v3')


class ConversationDelete(UUIDModel):
    """
    ConversationDelete is to record a user deleting a Conversation
    """
    user = models.ForeignKey(AUTH_USER_MODEL, related_name='deleted_conversations_set')
    conversation = models.ForeignKey('shoutit.Conversation', related_name='deleted_set')

    class Meta(UUIDModel.Meta):
        # so the user can mark the conversation as 'deleted' only once
        unique_together = ('user', 'conversation')


class Message(Action):
    """
    Message is a message from user into a Conversation
    """
    conversation = models.ForeignKey('shoutit.Conversation', related_name='messages')
    read_by = models.ManyToManyField(AUTH_USER_MODEL, blank=True, through='shoutit.MessageRead', related_name='read_messages')
    deleted_by = models.ManyToManyField(AUTH_USER_MODEL, blank=True, through='shoutit.MessageDelete',
                                        related_name='deleted_messages')
    text = models.CharField(null=True, blank=True, max_length=2000,
                            help_text="The text body of this message, could be None if the message has attachments")

    notifications = GenericRelation('shoutit.Notification', related_query_name='message')

    def __unicode__(self):
        return "%s  at:%s" % (self.summary, self.created_at_unix)

    def clean(self):
        none_to_blank(self, ['text'])

    @property
    def summary(self):
        return (getattr(self, 'text') or 'attachment')[:30]

    @property
    def attachments(self):
        return MessageAttachment.objects.filter(message_id=self.id)

    @property
    def has_attachments(self):
        return MessageAttachment.exists(message_id=self.id)

    @property
    def is_first(self):
        first_id = self.conversation.messages.all().order_by('created_at')[:1].values_list('id', flat=True)[0]
        return self.id == first_id

    @property
    def contributors(self):
        return self.conversation.contributors

    def can_contribute(self, user):
        return self.conversation.can_contribute(user)

    def is_read(self, user):
        return MessageRead.exists(user=user, message=self, conversation=self.conversation)

    @property
    def read_by_objects(self):
        read_by = [
            {'profile_id': self.user_id, 'read_at': self.created_at_unix}
        ]
        for read in self.read_set.all().values('user_id', 'created_at'):
            read_by.append({'profile_id': read['user_id'], 'read_at': date_unix(read['created_at'])})
        return read_by

    def mark_as_read(self, user, trigger_stats_update=True):
        try:
            MessageRead.objects.create(user=user, message_id=self.id, conversation_id=self.conversation_id)

            if trigger_stats_update:
                # Trigger `stats_update` on Pusher
                from ..controllers import pusher_controller
                pusher_controller.trigger_stats_update(user, 'v3')
        except IntegrityError:
            pass

    def mark_as_unread(self, user):
        try:
            MessageRead.objects.get(user=user, message_id=self.id, conversation_id=self.conversation_id).delete()
        except MessageRead.DoesNotExist:
            pass

    @property
    def track_properties(self):
        conversation = self.conversation
        properties = {
            'id': self.pk,
            'profile': self.user_id,
            'type': 'text' if self.text else 'attachment',
            'conversation_id': self.conversation_id,
            'conversation_type': conversation.get_type_display(),
            'is_first': self.is_first,
            'Country': self.get_country_display(),
            'Region': self.state,
            'City': self.city,
            'api_client': getattr(self, 'api_client', None),
            'api_version': getattr(self, 'api_version', None),
        }
        if properties['type'] == 'attachment':
            first_attachment = self.attachments.first()
            if first_attachment:
                properties.update({'attachment_type': first_attachment.summary})
        if conversation.about and conversation.type == CONVERSATION_TYPE_ABOUT_SHOUT:
            properties.update({'shout': conversation.about.pk})
            if conversation.about.is_sss:
                properties.update({'about_sss': True})
        return properties


@receiver(post_save, sender=Message)
def post_save_message(sender, instance=None, created=False, **kwargs):
    if created:
        # Save the attachments
        from ..controllers.message_controller import save_message_attachments
        attachments = getattr(instance, 'raw_attachments', [])
        save_message_attachments(instance, attachments)

        # Push the message to the conversation presence channel
        from ..controllers import notifications_controller, pusher_controller
        pusher_controller.trigger_new_message(instance, version='v3')

        # Update the conversation without sending `conversation_update` pusher event
        conversation = instance.conversation
        conversation.last_message = instance
        conversation.notify = False
        conversation.save()

        # Todo: move the logic below on a queue
        # Add the message user to conversation users if he isn't already
        try:
            conversation.users.add(instance.user)
        except IntegrityError:
            pass

        # Notify the other participants
        for to_user in conversation.contributors:
            if instance.user and instance.user != to_user:
                notifications_controller.notify_user_of_message(to_user, instance)

        # Track the message on MixPanel
        if instance.user:
            track_new_message(instance)


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


@receiver(post_save, sender=MessageRead)
def post_save_message_read(sender, instance=None, created=False, **kwargs):
    if created:
        from ..controllers import pusher_controller
        # Trigger `new_read_by` event in the conversation channel
        pusher_controller.trigger_new_read_by(message=instance.message, version='v3')
        # Trigger `stats_update` event in the reader profile channel
        pusher_controller.trigger_stats_update(user=instance.user, version='v3')


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
    # media type
    images = ArrayField(models.URLField(), default=list, blank=True)
    videos = models.ManyToManyField('shoutit.Video', blank=True)

    def __unicode__(self):
        return self.pk + " for message: " + self.message.pk

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

    @property
    def summary(self):
        _summary = self.get_type_display()
        if self.type == MESSAGE_ATTACHMENT_TYPE_MEDIA:
            images_count = len(self.images)
            videos_count = self.videos.count()
            if images_count and videos_count:
                _summary = "%s photo(s) | %s video(s)" % (images_count, videos_count)
            elif images_count:
                _summary = "%s photo(s)" % images_count
            elif videos_count:
                _summary = "%s videos(s)" % videos_count
        return _summary


class Notification(UUIDModel, AttachedObjectMixin):
    type = models.IntegerField(default=NOTIFICATION_TYPE_LISTEN.value, choices=NotificationType.choices)
    to_user = models.ForeignKey(AUTH_USER_MODEL, related_name='notifications')
    is_read = models.BooleanField(default=False)
    from_user = models.ForeignKey(AUTH_USER_MODEL, related_name='+', null=True, blank=True, default=None)

    def __unicode__(self):
        return self.pk + ": " + self.get_type_display()

    def mark_as_read(self):
        self.is_read = True
        self.save(update_fields=['is_read'])

        # Trigger `stats_update` on Pusher
        from ..controllers import pusher_controller
        pusher_controller.trigger_stats_update(self.to_user, 'v3')


class Report(UUIDModel, AttachedObjectMixin):
    user = models.ForeignKey(AUTH_USER_MODEL, related_name='reports')
    text = models.TextField(null=True, blank=True, max_length=300)
    type = models.IntegerField(default=REPORT_TYPE_GENERAL.value, choices=ReportType.choices)
    is_solved = models.BooleanField(default=False)
    is_disabled = models.BooleanField(default=False)

    def __unicode__(self):
        return "From user:%s about: %s:%s" % (self.user.pk, self.get_type_display(), self.attached_object.pk)

    def clean(self):
        none_to_blank(self, ['text'])


class PushBroadcast(UUIDModel, AttachedObjectMixin):
    user = models.ForeignKey(AUTH_USER_MODEL, related_name='broadcasts')
    message = models.TextField(max_length=300, blank=True)
    conditions = JsonField(default=dict, blank=True)
    data = JsonField(default=dict, blank=True)

    def __unicode__(self):
        return self.pk
