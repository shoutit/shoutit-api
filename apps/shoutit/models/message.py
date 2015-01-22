from django.db import models
from django.conf import settings

from common.constants import ReportType, NotificationType, NOTIFICATION_TYPE_LISTEN
from apps.shoutit.models.base import UUIDModel, AttachedObjectMixin
from apps.shoutit.models.post import Trade

AUTH_USER_MODEL = getattr(settings, 'AUTH_USER_MODEL')


class Conversation(UUIDModel):
    def __unicode__(self):
        return unicode(self.pk)

    FromUser = models.ForeignKey(AUTH_USER_MODEL, related_name='+')
    ToUser = models.ForeignKey(AUTH_USER_MODEL, related_name='+')
    AboutPost = models.ForeignKey(Trade, related_name='+')
    IsRead = models.BooleanField(default=False)
    VisibleToRecivier = models.BooleanField(default=True)
    VisibleToSender = models.BooleanField(default=True)


class Message(UUIDModel):
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


class MessageAttachment(UUIDModel, AttachedObjectMixin):

    def __unicode__(self):
        return self.pk + "for message: " + self.message.pk

    message = models.ForeignKey(Message, related_name='attachments')


class Notification(UUIDModel, AttachedObjectMixin):

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
