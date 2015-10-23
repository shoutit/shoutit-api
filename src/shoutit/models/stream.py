from __future__ import unicode_literals
from django.apps import apps
from django.core.exceptions import ValidationError
from django.db.models.signals import post_save, pre_delete, pre_save
from django.db import models, IntegrityError
from django.dispatch import receiver
from django.conf import settings
from common.constants import (
    StreamType, Stream_TYPE_PROFILE,
    ListenType, LISTEN_TYPE_PROFILE, LISTEN_TYPE_PAGE, LISTEN_TYPE_TAG)
from shoutit.models.action import Action
from shoutit.models.base import UUIDModel, AttachedObjectMixin, LocationMixin
from shoutit.utils import debug_logger, track

AUTH_USER_MODEL = getattr(settings, 'AUTH_USER_MODEL')


class Stream(UUIDModel, AttachedObjectMixin):
    type = models.SmallIntegerField(null=False, db_index=True, choices=StreamType.choices)
    posts = models.ManyToManyField('shoutit.Post', through='shoutit.StreamPost', related_name='streams')
    listeners = models.ManyToManyField(AUTH_USER_MODEL, through='shoutit.Listen', through_fields=('stream', 'user'), related_name='listening')

    class Meta(UUIDModel.Meta):
        unique_together = ('content_type', 'object_id', 'type')  # so each model can have only one stream

    def __unicode__(self):
        return "%s: %s" % (self.pk, repr(self.attached_object).decode('utf8'))

    def __init__(self, *args, **kwargs):
        # attached_object is the owner
        if 'attached_object' in kwargs and 'type' not in kwargs:
            attached_object = kwargs['attached_object']
            kwargs['type'] = StreamType.texts[attached_object.__class__.__name__]
        super(Stream, self).__init__(*args, **kwargs)

    def add_post(self, post):
        try:
            StreamPost.create(stream=self, post=post)
        except (ValidationError, IntegrityError):
            # the post exists already in this stream
            pass

    def remove_post(self, post):
        try:
            StreamPost.objects.get(stream=self, post=post).delete()
        except StreamPost.DoesNotExist:
            pass

    @property
    def owner(self):
        return self.attached_object

    @property
    def type_name(self):
        return StreamType.values[self.type]


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
        return Listen.objects.filter(user=user, stream=self.stream).exists()

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
        Stream.create(id=instance.id, attached_object=instance)
        debug_logger.debug('Created Stream for: <%s: %s>' % (instance.model_name, instance))


@receiver(pre_delete)
def delete_attached_stream(sender, instance, using, **kwargs):
    """
    remove the stream before deleting the instance
    """
    if not issubclass(sender, StreamMixin):
        return

    debug_logger.debug('Deleted Stream for: <%s: %s>' % (sender.__name__, instance))
    # GenericRelation in StreamMixin makes sure that Stream is being deleted when deleting the instance itself
    # so no need for us to explicitly do that
    # instance.stream.delete()


class AbstractStreamPost(UUIDModel, LocationMixin):
    stream = models.ForeignKey('shoutit.Stream')
    post = models.ForeignKey('shoutit.Post')
    published_at = models.DateTimeField(auto_now_add=True, db_index=True)
    rank_1 = models.IntegerField(default=0)
    rank_2 = models.IntegerField(default=0)
    rank_3 = models.IntegerField(default=0)

    class Meta(UUIDModel.Meta):
        abstract = True


class StreamPost(models.Model):
    stream = models.ForeignKey('shoutit.Stream')
    post = models.ForeignKey('shoutit.Post')

    class Meta:
        db_table = 'shoutit_stream_posts'


@receiver(pre_save)
def abstract_stream_post_pre_save(sender, instance=None, created=False, **kwargs):
    if not issubclass(sender, AbstractStreamPost):
        return
    # published_at
    instance.published_at = instance.post.date_published
    # location
    from shoutit.controllers import location_controller
    location_controller.update_object_location(instance, instance.post.location, save=False)
    # rank
    instance.rank_1 = instance.post.priority


class Listen(Action):
    stream = models.ForeignKey('shoutit.Stream')

    class Meta(UUIDModel.Meta):
        unique_together = ('user', 'stream')  # so the user can listen to the stream only once

    def __init__(self, *args, **kwargs):
        super(Action, self).__init__(*args, **kwargs)
        self._meta.get_field('user').blank = False

    def __unicode__(self):
        return "%s to %s" % (self.user, repr(self.stream).decode('utf8'))

    @property
    def track_properties(self):
        type_name = self.stream.type_name.lower()
        properties = {
            'type': type_name,
            type_name: str(self.stream.owner.user) if self.stream.type == Stream_TYPE_PROFILE else self.stream.owner.name

        }
        return properties


@receiver(post_save, sender=Listen)
def post_save_listen(sender, instance=None, created=False, **kwargs):
    if created:
        track(instance.user.pk, 'new_listen', instance.track_properties)


class Listen2(Action):
    type = models.SmallIntegerField(choices=ListenType.choices)
    target = models.CharField(db_index=True, max_length=36)

    class Meta:
        unique_together = ('user', 'type', 'target')

    def __init__(self, *args, **kwargs):
        super(Action, self).__init__(*args, **kwargs)
        self._meta.get_field('user').blank = False

    def __unicode__(self):
        return "User: %s to %s: %s" % (self.user_id, self.get_type_display(), self.target)

    @property
    def target_object(self):
        model = apps.get_model("shoutit", self.get_type_display())
        return model.objects.get(**{Listen2.target_attr(self.type): self.target})

    @classmethod
    def target_and_type_from_object(cls, obj):
        listen_type = ListenType.texts[obj.model_name]
        return listen_type, getattr(obj, Listen2.target_attr(listen_type))

    @classmethod
    def target_attr(cls, listen_type):
        return {
            LISTEN_TYPE_PROFILE: 'pk',
            LISTEN_TYPE_PAGE: 'pk',
            LISTEN_TYPE_TAG: 'name',
        }[listen_type]
