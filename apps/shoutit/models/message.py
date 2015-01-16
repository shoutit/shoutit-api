from django.db import models
from django.conf import settings

from common.constants import ReportType, NotificationType, NOTIFICATION_TYPE_LISTEN
from apps.shoutit.models.base import UUIDModel, AttachedObjectMixin
from apps.shoutit.models.post import Trade

AUTH_USER_MODEL = getattr(settings, 'AUTH_USER_MODEL')


class Conversation(UUIDModel):
    class Meta:
        app_label = 'shoutit'

    def __unicode__(self):
        return unicode(self.pk)

    FromUser = models.ForeignKey(AUTH_USER_MODEL, related_name='+')
    ToUser = models.ForeignKey(AUTH_USER_MODEL, related_name='+')
    AboutPost = models.ForeignKey(Trade, related_name='+')
    IsRead = models.BooleanField(default=False)
    VisibleToRecivier = models.BooleanField(default=True)
    VisibleToSender = models.BooleanField(default=True)


class Message(UUIDModel):
    class Meta:
        app_label = 'shoutit'

    def __unicode__(self):
        try:
            return unicode(self.pk) + ": " + "(" + unicode(self.FromUser) + " <=>> " + unicode(self.ToUser) + "):" + self.Text
        except AttributeError:
            return unicode(self.pk)

    Conversation = models.ForeignKey(Conversation, related_name='Messages')
    FromUser = models.ForeignKey(AUTH_USER_MODEL, related_name='received_messages')
    ToUser = models.ForeignKey(AUTH_USER_MODEL, related_name='sent_messages')
    Text = models.TextField(null=True, blank=False)
    IsRead = models.BooleanField(default=False)
    VisibleToRecivier = models.BooleanField(default=True)
    VisibleToSender = models.BooleanField(default=True)
    DateCreated = models.DateTimeField(auto_now_add=True)


class Conversation2(UUIDModel):
    """
    Conversation2 will introduce group chat where a conversation can have many users, each will contribute by creating Message2
    """
    class Meta:
        app_label = 'shoutit'

    users = models.ManyToManyField(AUTH_USER_MODEL, related_name='conversations2')


class Message2(UUIDModel):
    """
    Message2 is a message from user into a Conversation2
    """
    class Meta:
        app_label = 'shoutit'

    user = models.ForeignKey(AUTH_USER_MODEL, related_name='+')
    conversation = models.ForeignKey(Conversation2, related_name='messages2')
    read_by = models.ManyToManyField(AUTH_USER_MODEL, through='Message2Read', related_name='read_messages2')
    deleted_by = models.ManyToManyField(AUTH_USER_MODEL, through='Message2Deleted', related_name='deleted_messages2')


class Message2Read(UUIDModel):
    """
    Message2Read is to record a user reading a Message2
    """
    class Meta:
        app_label = 'shoutit'

    user = models.ForeignKey(AUTH_USER_MODEL)
    message = models.ForeignKey(Message2, related_name='read_by_set')
    conversation = models.ForeignKey(Conversation2, related_name='read_by_set')


class Message2Deleted(UUIDModel):
    """
    Message2Read is to record a user deleting a Message2
    """
    class Meta:
        app_label = 'shoutit'

    user = models.ForeignKey(AUTH_USER_MODEL)
    message = models.ForeignKey(Message2, related_name='deleted_by_set')
    conversation = models.ForeignKey(Conversation2, related_name='deleted_by_set')


class MessageAttachment(UUIDModel, AttachedObjectMixin):
    class Meta:
        app_label = 'shoutit'

    message = models.ForeignKey(Message, related_name='attachments')

    def __unicode__(self):
        return self.pk + "for message: " + self.message.pk


class Notification(UUIDModel, AttachedObjectMixin):
    class Meta:
        app_label = 'shoutit'

    def __unicode__(self):
        return self.pk + ": " + self.Text

    ToUser = models.ForeignKey(AUTH_USER_MODEL, related_name='Notifications')
    FromUser = models.ForeignKey(AUTH_USER_MODEL, related_name='+', null=True, default=None)
    IsRead = models.BooleanField(default=False)
    Type = models.IntegerField(default=NOTIFICATION_TYPE_LISTEN.value, choices=NotificationType.choices)
    DateCreated = models.DateTimeField(auto_now_add=True)

    @property
    def Text(self):
        return NotificationType.values[self.Type]

    def MarkAsRead(self):
        self.IsRead = True
        self.save()


class Report(UUIDModel, AttachedObjectMixin):
    class Meta:
        app_label = 'shoutit'

    def __unicode__(self):
        return "From user:%s about: %s:%s" % (self.user.pk, self.Type(), self.attached_object.pk)

    user = models.ForeignKey(AUTH_USER_MODEL, related_name='Reports')
    Text = models.TextField(default='', max_length=300)
    Type = models.IntegerField(default=0)
    IsSolved = models.BooleanField(default=False)
    IsDisabled = models.BooleanField(default=False)
    DateCreated = models.DateTimeField(auto_now_add=True)

    @property
    def Type(self):
        return ReportType.values[self.Type]
