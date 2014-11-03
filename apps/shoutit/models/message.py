from django.db import models
from django.contrib.auth.models import User
from apps.shoutit.constants import ReportType, NotificationType
from django.contrib.contenttypes import generic
from django.contrib.contenttypes.models import ContentType

from models import Trade

__author__ = 'SYRON'


class Conversation(models.Model):
    class Meta:
        app_label = 'shoutit'

    def __unicode__(self):
        return unicode(self.id)

    FromUser = models.ForeignKey(User, related_name='+')
    ToUser = models.ForeignKey(User, related_name='+')
    AboutPost = models.ForeignKey(Trade, related_name='+')
    IsRead = models.BooleanField(default=False)
    VisibleToRecivier = models.BooleanField(default=True)
    VisibleToSender = models.BooleanField(default=True)


class Message(models.Model):
    class Meta:
        app_label = 'shoutit'

    def __unicode__(self):
        try:
            return unicode(self.id) + ": " + "(" + unicode(self.FromUser) + " <=>> " + unicode(self.ToUser) + "):" + self.Text
        except:
            return unicode(self.id)

    Conversation = models.ForeignKey(Conversation, related_name='Messages')
    FromUser = models.ForeignKey(User, related_name='ReciviedMessages')
    ToUser = models.ForeignKey(User, related_name='SentMessages')
    Text = models.TextField(null=True, blank=False)
    IsRead = models.BooleanField(default=False)
    VisibleToRecivier = models.BooleanField(default=True)
    VisibleToSender = models.BooleanField(default=True)
    DateCreated = models.DateTimeField(auto_now_add=True)


class MessageAttachment(models.Model):

    class Meta:
        app_label = 'shoutit'

    message = models.ForeignKey(Message, related_name='attachments')

    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    content_object = generic.GenericForeignKey('content_type', 'object_id')

    def __unicode__(self):
        return ''


class Notification(models.Model):
    class Meta:
        app_label = 'shoutit'

    def __unicode__(self):
        return unicode(self.id) + ": " + self.Text

    ToUser = models.ForeignKey(User, related_name='Notifications')
    FromUser = models.ForeignKey(User, related_name='+', null=True, default=None)
    IsRead = models.BooleanField(default=False)
    Type = models.IntegerField(default=0)
    DateCreated = models.DateTimeField(auto_now_add=True)

    content_type = models.ForeignKey(ContentType, null=True)
    object_pk = models.TextField(null=True)
    AttachedObject = generic.GenericForeignKey(fk_field='object_pk')

    @property
    def Text(self):
        return NotificationType.values[self.Type]

    def MarkAsRead(self):
        self.IsRead = True
        self.save()


class Report(models.Model):
    class Meta:
        app_label = 'shoutit'

    def __unicode__(self):
        return 'From : ' + self.Type()

    User = models.ForeignKey(User, related_name='Reports')
    Text = models.TextField(default='', max_length=300)
    Type = models.IntegerField(default=0)
    IsSolved = models.BooleanField(default=False)
    IsDisabled = models.BooleanField(default=False)
    DateCreated = models.DateTimeField(auto_now_add=True)

    content_type = models.ForeignKey(ContentType, null=True)
    object_pk = models.TextField(null=True)
    AttachedObject = generic.GenericForeignKey(fk_field='object_pk')

    @property
    def Type(self):
        return ReportType.values[self.Type]
