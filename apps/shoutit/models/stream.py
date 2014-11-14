from django.db import models

from apps.shoutit.constants import *


class Stream(models.Model):
    class Meta:
        app_label = 'shoutit'

    def __unicode__(self):
        return unicode(self.id) + ' ' + self.GetTypeText() + ' (' + unicode(self.GetOwner()) + ')'

    Type = models.IntegerField(default=0, db_index=True)

    def GetOwner(self):
        owner = None
        try:
            if self.Type == STREAM_TYPE_TAG:
                owner = self.OwnerTag
            elif self.Type == STREAM_TYPE_USER:
                owner = self.OwnerUser
            elif self.Type == STREAM_TYPE_BUSINESS:
                owner = self.OwnerBusiness
            elif self.Type == STREAM_TYPE_RECOMMENDED:
                owner = self.InitShoutRecommended
            elif self.Type == STREAM_TYPE_RELATED:
                owner = self.InitShoutRelated
        except AttributeError, e:
            print e.message
            return None
        return owner

    def GetTypeText(self):
        stream_type = u'None'
        if self.Type == STREAM_TYPE_TAG:
            stream_type = unicode(STREAM_TYPE_TAG)
        elif self.Type == STREAM_TYPE_USER:
            stream_type = unicode(STREAM_TYPE_USER)
        elif self.Type == STREAM_TYPE_BUSINESS:
            stream_type = unicode(STREAM_TYPE_BUSINESS)
        elif self.Type == STREAM_TYPE_RECOMMENDED:
            stream_type = unicode(STREAM_TYPE_RECOMMENDED)
        elif self.Type == STREAM_TYPE_RELATED:
            stream_type = unicode(STREAM_TYPE_RELATED)
        return stream_type

    def PublishShout(self, shout):
        self.Posts.add(shout)
        self.save()

    def UnPublishShout(self, shout):
        self.Posts.remove(shout)
        self.save()



######### experiment new stream
from apps.shoutit.models import User
from django.contrib.contenttypes.generic import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db.models.signals import post_save, pre_delete, post_delete
from django.dispatch import receiver


class Stream2(models.Model):

    class Meta:
        app_label = 'shoutit'
        unique_together = ('content_type', 'object_id', 'type')  # so each model can have only one stream

    def __unicode__(self):
        return unicode(self.id) + ':' + StreamType2.values[self.type] + ' (' + unicode(self.owner) + ')'

    def __init__(self, *args, **kwargs):
        if 'owner' in kwargs and 'type' not in kwargs:
            owner = kwargs['owner']
            kwargs['type'] = StreamType2.texts[owner.__class__.__name__]
        super(Stream2, self).__init__(*args, **kwargs)

    type = models.SmallIntegerField(null=False, db_index=True, choices=StreamType2.choices)
    # owner
    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    owner = GenericForeignKey('content_type', 'object_id')

    posts = models.ManyToManyField('Post', related_name='streams')
    listeners = models.ManyToManyField(User, through='Listen', related_name='listening')


class Stream2Mixin(object):
    @property
    def stream2(self):
        if not hasattr(self, '_stream2'):
            ct = ContentType.objects.get_for_model(self.__class__)
            try:
                self._stream2 = Stream2.objects.get(content_type__pk=ct.id, object_id=self.id)
            except Stream2.DoesNotExist:
                return None
        return self._stream2


class Listen(models.Model):
    class Meta:
        app_label = 'shoutit'
        unique_together = ('listener', 'stream')  # so the user can follow the stream only once

    listener = models.ForeignKey(User)
    stream = models.ForeignKey(Stream2)
    date_listened = models.DateTimeField(auto_now_add=True)

