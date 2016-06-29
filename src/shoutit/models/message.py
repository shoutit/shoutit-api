# -*- coding: utf-8 -*-
"""

"""
from __future__ import unicode_literals

from collections import OrderedDict

from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.contrib.contenttypes.fields import GenericRelation
from django.contrib.postgres.fields import ArrayField
from django.db import models, IntegrityError, transaction
from django.db.models import Q, Count
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils.translation import ugettext_lazy as _
from django_pgjson.fields import JsonField
from pydash import strings

from common.constants import (
    ReportType, NotificationType, NOTIFICATION_TYPE_LISTEN, MessageAttachmentType, MESSAGE_ATTACHMENT_TYPE_SHOUT,
    ConversationType, MESSAGE_ATTACHMENT_TYPE_LOCATION, REPORT_TYPE_GENERAL, CONVERSATION_TYPE_ABOUT_SHOUT,
    CONVERSATION_TYPE_PUBLIC_CHAT, NOTIFICATION_TYPE_MESSAGE, MESSAGE_ATTACHMENT_TYPE_MEDIA,
    MESSAGE_ATTACHMENT_TYPE_PROFILE, CONVERSATION_TYPE_CHAT, NOTIFICATION_TYPE_MISSED_VIDEO_CALL,
    NOTIFICATION_TYPE_INCOMING_VIDEO_CALL, NOTIFICATION_TYPE_CREDIT_TRANSACTION, NOTIFICATION_TYPE_SHOUT_LIKE)
from common.utils import date_unix
from .auth import User
from .action import Action
from .base import UUIDModel, AttachedObjectMixin, APIModelMixin, NamedLocationMixin
from ..utils import none_to_blank

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
    blocked = ArrayField(models.UUIDField(), default=list, blank=True)
    deleted_by = models.ManyToManyField(AUTH_USER_MODEL, through='shoutit.ConversationDelete',
                                        related_name='deleted_conversations')
    last_message = models.OneToOneField('shoutit.Message', related_name='+', null=True, blank=True,
                                        on_delete=models.SET_NULL)

    def __unicode__(self):
        return "%s at:%s" % (self.pk, self.modified_at_unix)

    def clean(self):
        none_to_blank(self, ['icon', 'subject'])

    @property
    def about(self):
        return self.attached_object

    @property
    def messages_count(self):
        return self.messages.exclude(user=None).count()

    def unread_messages(self, user):
        if isinstance(user, AnonymousUser):
            return self.messages.none()
        return self.messages.exclude(read_set__user=user).exclude(Q(user=user) | Q(user=None))

    def display(self, user):
        # Todo (mo): Optimize!
        title = self.subject
        is_contributor = self.contributors.only('id').filter(id=user.id).exists()
        contributors_summary = self.contributors.exclude(id=user.id).select_related('profile', 'page')[:5]
        contributors_summary_names = map(lambda u: u.name, contributors_summary)
        contributors_summary_len = len(contributors_summary)
        if contributors_summary_len == 0:
            sub_title = "You only" if is_contributor else ''
        else:
            sub_title = ", ".join(contributors_summary_names)
            if is_contributor and (contributors_summary_len > 1 or self.type == CONVERSATION_TYPE_PUBLIC_CHAT):
                sub_title = "You, " + sub_title
        image = self.icon
        last_message_summary = self.last_message.summary if self.last_message else None

        if self.type == CONVERSATION_TYPE_ABOUT_SHOUT and self.about:
            title = self.about.title
            image = self.about.thumbnail
        elif self.type == CONVERSATION_TYPE_CHAT:
            if not title:
                title = sub_title
                sub_title = ''
            if not image:
                if contributors_summary:
                    image = contributors_summary[0].ap.image
                elif user.is_authenticated():
                    image = user.ap.image

        dis = OrderedDict([
            ('title', title),
            ('sub_title', sub_title),
            ('last_message_summary', last_message_summary),
            ('image', image),
        ])
        return dis

    def attachments_count(self):
        counts = self.messages_attachments.values('type').annotate(total=Count('type'))
        available_counts = dict([(MessageAttachmentType.values[c['type']], c['total']) for c in counts])
        all_counts = dict([(t, 0) for t in MessageAttachmentType.texts.keys()])
        all_counts.update(available_counts)
        return all_counts

    @property
    def contributors(self):
        return self.users.exclude(id__in=self.blocked)

    def can_contribute(self, user):
        if self.type == CONVERSATION_TYPE_PUBLIC_CHAT:
            return user.id not in self.blocked
        else:
            return user in self.contributors

    def is_admin(self, user):
        return user.id in self.admins

    def mark_as_deleted(self, user):
        # 0 - Mark all its messages as read
        self.mark_as_read(user)

        # 1 - record the deletion
        try:
            with transaction.atomic():
                ConversationDelete.objects.create(user=user, conversation=self)
        except IntegrityError:
            pass

        # 2 - remove the user from the list of users
        if user in self.contributors:
            self.users.remove(user)

        # 3 - create a system message saying the user has left the conversation
        # Todo (mo) [#i18n]: Allow returning system message in localized text
        text = _("%(name)s has left the conversation") % {'name': user.name}
        Message.objects.create(user=None, text=text, conversation=self)
        # Todo: track `conversation_delete` event?

    def mark_as_read(self, user):
        unread_messages = self.unread_messages(user)
        if not unread_messages:
            return

        # Read all the unread notifications about this conversation
        Notification.objects.filter(is_read=False, to_user=user, type=NOTIFICATION_TYPE_MESSAGE,
                                    message__conversation=self).update(is_read=True)

        # Trigger `stats_update` on Pusher
        from ..controllers import pusher_controller
        pusher_controller.trigger_stats_update(user, 'v3')

        # Read all the conversation's messages by other users that weren't read by the user before
        MessageRead.objects.bulk_create(
            map(lambda m: MessageRead(user=user, message=m, conversation=self), unread_messages)
        )

        # Todo: Optimize! bulk pusher events
        for message in unread_messages:
            pusher_controller.trigger_new_read_by(message=message, version='v3')

    def mark_as_unread(self, user):
        # Delete the last MessageRead only if it exits
        last_message_read = self.messages_read_set.filter(user=user).order_by('created_at').last()
        if last_message_read:
            last_message_read.delete()

    def add_profile(self, profile):
        from ..controllers import pusher_controller
        self.users.add(profile)
        pusher_controller.trigger_conversation_update(self, 'v3')

    def remove_profile(self, profile):
        from ..controllers import pusher_controller
        self.users.remove(profile)
        pusher_controller.trigger_conversation_update(self, 'v3')

    def promote_admin(self, profile):
        self.admins.append(profile.id)
        self.save(update_fields=['admins'])

    def block_profile(self, profile):
        if profile.id in self.admins:
            self.admins.remove(profile.id)
        self.blocked.append(profile.id)
        self.save(update_fields=['admins', 'blocked'])

    def unblock_profile(self, profile):
        self.blocked.remove(profile.id)
        self.save(update_fields=['blocked'])

    @property
    def media_attachments(self):
        return self.messages_attachments.filter(type=MESSAGE_ATTACHMENT_TYPE_MEDIA)

    @property
    def shout_attachments(self):
        from .post import Shout
        return (Shout.objects.filter(message_attachments__conversation=self)
                             .distinct())


@receiver(pre_save, sender=Conversation)
def pre_save_conversation(sender, instance=None, **kwargs):
    from ..controllers import location_controller

    if instance._state.adding and instance.creator:
        if instance.creator.id not in instance.admins:
            instance.admins.append(instance.creator.id)
        if not instance.is_named_location:
            location_controller.update_object_location(instance, instance.creator.location, save=False)


@receiver(post_save, sender=Conversation)
def post_save_conversation(sender, instance=None, created=False, **kwargs):
    from ..controllers import pusher_controller

    if created:
        if instance.type == CONVERSATION_TYPE_PUBLIC_CHAT:
            text = _("%(name)s created this public chat") % {'name': instance.creator.name}
            message = Message.create(save=False, user=None, text=text, conversation=instance)
            message.skip_post_save = True
            message.save()
            instance.last_message = message
            instance.notify = False
            instance.save()

    else:
        if getattr(instance, 'notify', True):
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
    read_by = models.ManyToManyField(AUTH_USER_MODEL, blank=True, through='shoutit.MessageRead',
                                     related_name='read_messages')
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
        # Todo: Create summary attribute and set it while saving
        text = getattr(self, 'text') or 'attachment'
        _summary = strings.truncate(text, 100, '', ' ')
        if self.user_id:
            return _("%(name)s: %(message)s") % {'name': self.user.name, 'message': _summary}
        else:
            return _summary

    @property
    def attachments(self):
        return MessageAttachment.objects.filter(message_id=self.id)

    @property
    def has_attachments(self):
        return MessageAttachment.exists(message_id=self.id)

    @property
    def is_first(self):
        first_id = self.conversation.messages.values_list('id', flat=True).order_by('created_at').first()
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
        # No read by for system messages
        if self.user_id is None:
            return []
        read_by = [
            {'profile_id': self.user_id, 'read_at': self.created_at_unix}
        ]
        for read in self.read_set.all().values('user_id', 'created_at'):
            read_by.append({'profile_id': read['user_id'], 'read_at': date_unix(read['created_at'])})
        return read_by

    def mark_as_read(self, user):
        try:
            with transaction.atomic():
                MessageRead.objects.create(user=user, message_id=self.id, conversation_id=self.conversation_id)
        except IntegrityError:
            pass
        else:
            from ..controllers import pusher_controller

            # Trigger `new_read_by` event in the conversation channel
            pusher_controller.trigger_new_read_by(message=self, version='v3')

            # Read the notifications about this message
            Notification.objects.filter(is_read=False, to_user=user, type=NOTIFICATION_TYPE_MESSAGE,
                                        message=self).update(is_read=True)

            # Trigger `stats_update` on Pusher
            pusher_controller.trigger_stats_update(user, 'v3')

    def mark_as_unread(self, user):
        user.read_messages_set.filter(message=self).delete()

    @property
    def track_properties(self):
        conversation = self.conversation
        properties = super(Message, self).track_properties
        properties.update({
            'conversation_id': self.conversation_id,
            'conversation_type': conversation.get_type_display(),
            'is_first': self.is_first,
        })
        if properties['type'] == 'attachment':
            first_attachment = self.attachments.first()
            if first_attachment:
                properties.update({'attachment_type': first_attachment.summary})
        if conversation.about and conversation.type == CONVERSATION_TYPE_ABOUT_SHOUT:
            properties.update({'shout': conversation.about.pk})
            if conversation.about.is_sss:
                properties.update({'about_sss': True})
        return properties

    def get_type_display(self):
        return 'text' if self.text else 'attachment'


@receiver(post_save, sender=Message)
def post_save_message(sender, instance=None, created=False, **kwargs):
    if created and not getattr(instance, 'skip_post_save', False):
        # Save the attachments
        from ..controllers.message_controller import save_message_attachments
        attachments = getattr(instance, 'raw_attachments', [])
        save_message_attachments(instance, attachments)

        # Push the message to the conversation presence channel
        from ..controllers import notifications_controller, pusher_controller
        pusher_controller.trigger_new_message(instance, version='v3')

        # Todo: move the logic below on a queue
        conversation = instance.conversation
        # Add the message user to conversation users if he isn't already
        try:
            with transaction.atomic():
                conversation.users.add(instance.user)
        except IntegrityError:
            pass

        # Notify the other participants
        for to_user in conversation.contributors:
            if instance.user and instance.user != to_user:
                notifications_controller.notify_user_of_message(to_user, instance)

        # Update the conversation which sends a `conversation_update` pusher event
        conversation.last_message = instance
        conversation.detailed = False  # Don't send detailed conversation in the push event
        conversation.save()

        # Track the message on MixPanel
        from ..controllers import mixpanel_controller
        if instance.user:
            mixpanel_controller.track_new_message(instance)


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
    # media type
    images = ArrayField(models.URLField(), default=list, blank=True)
    videos = models.ManyToManyField('shoutit.Video', blank=True)

    def __unicode__(self):
        return self.get_type_display()

    @property
    def shout(self):
        if self.type == MESSAGE_ATTACHMENT_TYPE_SHOUT:
            return self.attached_object
        else:
            return None

    @property
    def profile(self):
        if self.type == MESSAGE_ATTACHMENT_TYPE_PROFILE:
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
    type = models.IntegerField(choices=NotificationType.choices)
    to_user = models.ForeignKey(AUTH_USER_MODEL, related_name='notifications')
    is_read = models.BooleanField(default=False)
    from_user = models.ForeignKey(AUTH_USER_MODEL, null=True, blank=True, related_name='+')
    expires_at = models.DateTimeField(null=True, blank=True, db_index=True)

    def __unicode__(self):
        return "%s: %s" % (self.pk, self.get_type_display())

    @property
    def notification_type(self):
        return NotificationType.instance(self.type)

    @property
    def event_name(self):
        if self.notification_type.is_new_notification_type():
            name = str(NotificationType.new_notification())
        else:
            name = str(self.notification_type)
        return name

    @property
    def event_object(self):
        if self.notification_type.is_new_notification_type():
            obj = self
        else:
            obj = self.attached_object
        return obj

    @property
    def push_event_name(self):
        if self.notification_type.is_new_notification_push_type():
            name = str(NotificationType.new_notification())
        else:
            name = str(self.notification_type)
        return name

    @property
    def push_event_object(self):
        if self.notification_type.is_new_notification_push_type():
            obj = self
        else:
            obj = self.attached_object
        return obj

    def display(self):
        if hasattr(self, '_display'):
            return self._display

        title = _("Shoutit")
        text = None
        ranges = []
        image = None
        target = self.attached_object

        if self.type == NOTIFICATION_TYPE_LISTEN:
            name = self.attached_object.name
            text = _("%(name)s started listening to you") % {'name': name}
            ranges.append({'offset': text.index(name), 'length': len(name)})
            ranges.append({'offset': text.index(unicode(_('you'))), 'length': len('you')})
            image = self.attached_object.ap.image

        elif self.type == NOTIFICATION_TYPE_MESSAGE:
            # Todo (mo): is `ranges` needed for messages notifications?
            title = _("New message")
            name = self.attached_object.user.first_name if self.attached_object.user else 'Shoutit'
            text = self.attached_object.summary
            ranges.append({'offset': text.index(name), 'length': len(name)})
            image = self.attached_object.user.ap.image
            target = self.attached_object.conversation

        elif self.type == NOTIFICATION_TYPE_INCOMING_VIDEO_CALL:
            # Todo (mo): is `ranges` needed for incoming video call notifications?
            title = _("Incoming video call")
            name = self.attached_object.name
            text = _("%(name)s is calling you on Shoutit") % {'name': name}
            ranges.append({'offset': text.index(name), 'length': len(name)})
            image = self.attached_object.ap.image

        elif self.type == NOTIFICATION_TYPE_MISSED_VIDEO_CALL:
            title = _("Missed video call")
            name = self.attached_object.name
            text = _("You missed a call from %(name)s") % {'name': name}
            ranges.append({'offset': text.index(name), 'length': len(name)})
            image = self.attached_object.ap.image

        elif self.type == NOTIFICATION_TYPE_CREDIT_TRANSACTION:
            title = _("New Credit Transaction")
            text = self.attached_object.display()['text']
            setattr(self, '_app_url', 'shoutit://credit_transactions')
            setattr(self, '_web_url', None)

        elif self.type == NOTIFICATION_TYPE_SHOUT_LIKE:
            title = _('New Shout Like')
            name = self.from_user.name
            shout_title = self.attached_object.title
            text = _('%(name)s liked your shout %(title)s') % {'name': name, 'title': shout_title}
            ranges.append({'offset': text.index(name), 'length': len(name)})
            ranges.append({'offset': text.index(shout_title), 'length': len(shout_title)})
            image = self.from_user.ap.image

        ret = OrderedDict([
            ('title', title),
            ('text', text),
            ('ranges', ranges),
            ('image', image),
        ])

        if self.type == NOTIFICATION_TYPE_INCOMING_VIDEO_CALL:
            ret['alert_extra'] = {'action-loc-key': _('Answer')}
            ret['aps_extra'] = {'category': 'VIDEO_CALL_CATEGORY'}

        setattr(self, 'target', target)
        setattr(self, '_display', ret)
        return self._display

    @property
    def app_url(self):
        self.display()
        if hasattr(self, '_app_url'):
            return self._app_url
        elif hasattr(self, 'target'):
            return getattr(self.target, 'app_url', None)
        else:
            return None

    @property
    def web_url(self):
        self.display()
        if hasattr(self, '_web_url'):
            return self._web_url
        elif hasattr(self, 'target'):
            return getattr(self.target, 'web_url', None)
        else:
            return None

    def mark_as_read(self):
        self.is_read = True
        self.save(update_fields=['is_read'])

        # Trigger `stats_update` on Pusher
        from ..controllers import pusher_controller
        pusher_controller.trigger_stats_update(self.to_user, 'v3')


@property
def actual_notifications(self):
    """
    Notifications that are *not* of type `new_message` or `new_credit_transaction` aka "Notifications" for end users
    """
    excluded_types = [NOTIFICATION_TYPE_MESSAGE, NOTIFICATION_TYPE_CREDIT_TRANSACTION]
    return self.notifications.exclude(type__in=excluded_types).order_by('-created_at')
User.add_to_class('actual_notifications', actual_notifications)


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
        return "%s" % self.pk
