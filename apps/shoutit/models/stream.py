from django.db import models
from django.conf import settings

from common.constants import StreamType2
from common.constants import STREAM_TYPE_RECOMMENDED, STREAM_TYPE_BUSINESS, STREAM_TYPE_TAG, STREAM_TYPE_USER, STREAM_TYPE_RELATED
from apps.shoutit.models.base import UUIDModel, AttachedObjectMixin

AUTH_USER_MODEL = getattr(settings, 'AUTH_USER_MODEL')


class Stream(UUIDModel):
    class Meta:
        app_label = 'shoutit'

    def __unicode__(self):
        return unicode(self.pk) + ' ' + self.GetTypeText() + ' (' + unicode(self.GetOwner()) + ')'

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
from django.contrib.contenttypes.models import ContentType
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver


class Stream2(UUIDModel, AttachedObjectMixin):

    class Meta:
        app_label = 'shoutit'
        unique_together = ('content_type', 'object_id', 'type')  # so each model can have only one stream

    def __unicode__(self):
        return unicode(self.pk) + ':' + StreamType2.values[self.type] + ' (' + unicode(self.attached_object) + ')'

    def __init__(self, *args, **kwargs):
    # attached_object is the owner
        if 'attached_object' in kwargs and 'type' not in kwargs:
            attached_object = kwargs['attached_object']
            kwargs['type'] = StreamType2.texts[attached_object.__class__.__name__]
        super(Stream2, self).__init__(*args, **kwargs)

    type = models.SmallIntegerField(null=False, db_index=True, choices=StreamType2.choices)
    posts = models.ManyToManyField('Post', related_name='streams')
    listeners = models.ManyToManyField(AUTH_USER_MODEL, through='Listen', related_name='listening')


class Stream2Mixin(object):
    @property
    def stream2(self):
        if not hasattr(self, '_stream2'):
            ct = ContentType.objects.get_for_model(self.__class__)
            try:
                self._stream2 = Stream2.objects.get(content_type__pk=ct.pk, object_id=self.pk)
            except Stream2.DoesNotExist:
                return None
        return self._stream2


@receiver(post_save)
def attach_stream(sender, instance, created, raw, using, update_fields, **kwargs):
    if not issubclass(sender, Stream2Mixin):
        return
    # on new instance create stream and attach it
    if created:
        print 'post save on first time'

        # creating the stream
        stream2 = Stream2(attached_object=instance)
        stream2.save()


@receiver(pre_delete)
def delete_attached_stream(sender, instance, using, **kwargs):
    if not issubclass(sender, Stream2Mixin):
        return
    # before deleting remove the stream
    print 'pre_delete'
    instance.stream2.delete()


class Listen(UUIDModel):
    class Meta:
        app_label = 'shoutit'
        unique_together = ('listener', 'stream')  # so the user can follow the stream only once

    listener = models.ForeignKey(AUTH_USER_MODEL)
    stream = models.ForeignKey(Stream2)
    date_listened = models.DateTimeField(auto_now_add=True)

