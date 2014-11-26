from django.contrib.contenttypes.generic import GenericForeignKey
from django.db import models
from django.contrib.auth.models import User
from uuidfield import UUIDField
from apps.shoutit.constants import ReportType, NotificationType, NOTIFICATION_TYPE_LISTEN
from django.contrib.contenttypes import generic
from django.contrib.contenttypes.models import ContentType
from apps.shoutit.models.misc import UUIDModel

from apps.shoutit.models.post import Trade


class Conversation(UUIDModel):
    class Meta:
        app_label = 'shoutit'

    def __unicode__(self):
        return unicode(self.pk)

    FromUser = models.ForeignKey(User, related_name='+')
    ToUser = models.ForeignKey(User, related_name='+')
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
    FromUser = models.ForeignKey(User, related_name='received_messages')
    ToUser = models.ForeignKey(User, related_name='sent_messages')
    Text = models.TextField(null=True, blank=False)
    IsRead = models.BooleanField(default=False)
    VisibleToRecivier = models.BooleanField(default=True)
    VisibleToSender = models.BooleanField(default=True)
    DateCreated = models.DateTimeField(auto_now_add=True)


class MessageAttachment(UUIDModel):

    class Meta:
        app_label = 'shoutit'

    message = models.ForeignKey(Message, related_name='attachments')

    content_type = models.ForeignKey(ContentType)
    object_pk = UUIDField(auto=True, hyphenate=True, version=4)
    content_object = generic.GenericForeignKey('content_type', 'object_pk')

    def __unicode__(self):
        return ''


class Notification(UUIDModel):
    class Meta:
        app_label = 'shoutit'

    def __unicode__(self):
        return unicode(self.pk) + ": " + self.Text

    ToUser = models.ForeignKey(User, related_name='Notifications')
    FromUser = models.ForeignKey(User, related_name='+', null=True, default=None)
    IsRead = models.BooleanField(default=False)
    Type = models.IntegerField(default=NOTIFICATION_TYPE_LISTEN.value, choices=NotificationType.choices)
    DateCreated = models.DateTimeField(auto_now_add=True)

    content_type = models.ForeignKey(ContentType, null=True)
    object_pk = UUIDField(auto=True, hyphenate=True, version=4, null=True)

    attached_object = GenericForeignKey('content_type', 'object_pk')

    @property
    def Text(self):
        return NotificationType.values[self.Type]

    def MarkAsRead(self):
        self.IsRead = True
        self.save()


class Report(UUIDModel):
    class Meta:
        app_label = 'shoutit'

    def __unicode__(self):
        return 'From : ' + self.Type()

    user =  models.ForeignKey(User, related_name='Reports')
    Text = models.TextField(default='', max_length=300)
    Type = models.IntegerField(default=0)
    IsSolved = models.BooleanField(default=False)
    IsDisabled = models.BooleanField(default=False)
    DateCreated = models.DateTimeField(auto_now_add=True)

    content_type = models.ForeignKey(ContentType, null=True)
    object_pk = UUIDField(auto=True, hyphenate=True, version=4, null=True)
    attached_object = generic.GenericForeignKey(fk_field='object_pk')

    @property
    def Type(self):
        return ReportType.values[self.Type]
