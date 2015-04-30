from __future__ import unicode_literals
from django.db.models.signals import post_save, pre_delete
from django.db import models, IntegrityError
from django.dispatch import receiver
from django.conf import settings
from common.constants import StreamType
from shoutit.models.base import UUIDModel, AttachedObjectMixin
import logging
logger = logging.getLogger('shoutit.debug')
AUTH_USER_MODEL = getattr(settings, 'AUTH_USER_MODEL')


class Stream(UUIDModel, AttachedObjectMixin):
    type = models.SmallIntegerField(null=False, db_index=True, choices=StreamType.choices)
    posts = models.ManyToManyField('shoutit.Post', related_name='streams2')
    listeners = models.ManyToManyField(AUTH_USER_MODEL, through='shoutit.Listen', related_name='listening')

    class Meta(UUIDModel.Meta):
        unique_together = ('content_type', 'object_id', 'type')  # so each model can have only one stream

    def __unicode__(self):
        return unicode(self.pk) + ':' + StreamType.values[self.type] + ' (' + unicode(self.attached_object) + ')'

    def __init__(self, *args, **kwargs):
        # attached_object is the owner
        if 'attached_object' in kwargs and 'type' not in kwargs:
            attached_object = kwargs['attached_object']
            kwargs['type'] = StreamType.texts[attached_object.__class__.__name__]
        super(Stream, self).__init__(*args, **kwargs)

    def add_post(self, post):
        from shoutit.models import Post
        assert isinstance(post, Post)
        try:
            self.posts.add(post)
        except IntegrityError:
            # the post exists already in this stream
            pass

    def remove_post(self, post):
        from shoutit.models import Post
        assert isinstance(post, Post)
        self.posts.remove(post)

    @property
    def owner(self):
        return self.attached_object


class StreamMixin(models.Model):
    """
    Each model that uses this mixin should have this property with `related_query_name` set to the model name
    eg.:
    ```
    _stream = GenericRelation('shoutit.Stream', related_query_name='profile')
    ```
    this will make it easier to query streams based on attributes of their owners
    """
    class Meta:
        abstract = True

    @property
    def stream(self):
        try:
            return self._stream.get()
        except Stream.DoesNotExist:
            return None

    def is_listening(self, user):
        """
        Check whether user is listening to this object's stream or not
        """
        return Listen.objects.filter(listener=user, stream=self.stream).exists()

    @property
    def listeners_count(self):
        return self.stream.listeners.count()

@receiver(post_save)
def attach_stream(sender, instance, created, raw, using, update_fields, **kwargs):
    """
    create stream and attach it to newly created instance
    """
    if not issubclass(sender, StreamMixin):
        return
    if created:
        stream = Stream(attached_object=instance)
        stream.save()
        logger.debug('Created Stream for: <%s: %s>' % (sender.__name__, instance))


@receiver(pre_delete)
def delete_attached_stream(sender, instance, using, **kwargs):
    """
    remove the stream before deleting the instance
    """
    if not issubclass(sender, StreamMixin):
        return

    logger.debug('Deleted Stream for: <%s: %s>' % (sender.__name__, instance))
    # GenericRelation in StreamMixin makes sure that Stream is being deleted when deleting the instance itself
    # so no need for us to explicitly do that
    # instance.stream.delete()


class Listen(UUIDModel):
    listener = models.ForeignKey(AUTH_USER_MODEL)
    stream = models.ForeignKey('shoutit.Stream')
    date_listened = models.DateTimeField(auto_now_add=True)

    class Meta(UUIDModel.Meta):
        unique_together = ('listener', 'stream')  # so the user can listen to the stream only once

