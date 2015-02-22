from django.db import models, IntegrityError
from django.conf import settings

from common.constants import StreamType2
from common.constants import STREAM_TYPE_RECOMMENDED, STREAM_TYPE_BUSINESS, STREAM_TYPE_TAG, STREAM_TYPE_USER, STREAM_TYPE_RELATED
import shoutit
from shoutit.models.base import UUIDModel, AttachedObjectMixin


AUTH_USER_MODEL = getattr(settings, 'AUTH_USER_MODEL')


class Stream(UUIDModel):
    Type = models.IntegerField(default=0, db_index=True)

    def __unicode__(self):
        return unicode(self.pk) + ' ' + self.GetTypeText() + ' (' + unicode(self.GetOwner()) + ')'

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


# todo: remove in favor of Listen
class FollowShip(UUIDModel):
    follower = models.ForeignKey('shoutit.Profile')
    stream = models.ForeignKey('shoutit.Stream')
    date_followed = models.DateTimeField(auto_now_add=True)
    state = models.IntegerField(default=0, db_index=True)

    def __unicode__(self):
        return unicode(self.pk) + ": " + unicode(self.follower) + " @ " + unicode(self.stream)

# ######## experiment new stream ######### #
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver


class Stream2(UUIDModel, AttachedObjectMixin):
    type = models.SmallIntegerField(null=False, db_index=True, choices=StreamType2.choices)
    posts = models.ManyToManyField('shoutit.Post', related_name='streams2')
    listeners = models.ManyToManyField(AUTH_USER_MODEL, through='shoutit.Listen', related_name='listening')

    class Meta(UUIDModel.Meta):
        unique_together = ('content_type', 'object_id', 'type')  # so each model can have only one stream

    def __unicode__(self):
        return unicode(self.pk) + ':' + StreamType2.values[self.type] + ' (' + unicode(self.attached_object) + ')'

    def __init__(self, *args, **kwargs):
        # attached_object is the owner
        if 'attached_object' in kwargs and 'type' not in kwargs:
            attached_object = kwargs['attached_object']
            kwargs['type'] = StreamType2.texts[attached_object.__class__.__name__]
        super(Stream2, self).__init__(*args, **kwargs)

    def add_post(self, post):
        assert isinstance(post, shoutit.models.Post)
        try:
            self.posts.add(post)
            post.refresh_streams2_ids()
        except IntegrityError:
            # the post exists already in this stream2
            pass

    def remove_post(self, post):
        assert isinstance(post, shoutit.models.Post)
        self.posts.remove(post)
        post.refresh_streams2_ids()

    @property
    def owner(self):
        return self.attached_object


class Stream2Mixin(models.Model):
    """
    Each model that uses this mixin should have this property with `related_query_name` set to the model name
    eg.:
    ```
    _stream2 = GenericRelation('shoutit.Stream2', related_query_name='profile')
    ```
    this will make it easier to query streams based on attributes of their owners
    """
    class Meta:
        abstract = True

    @property
    def stream2(self):
        try:
            return self._stream2.get()
        except Stream2.DoesNotExist:
            return None


@receiver(post_save)
def attach_stream(sender, instance, created, raw, using, update_fields, **kwargs):
    """
    create stream and attach it to newly created instance
    """
    if not issubclass(sender, Stream2Mixin):
        return
    if created:
        print 'Creating Stream2 for: <%s: %s>' % (sender.__name__, instance)
        stream2 = Stream2(attached_object=instance)
        stream2.save()


@receiver(pre_delete)
def delete_attached_stream(sender, instance, using, **kwargs):
    """
    remove the stream before deleting the instance
    """
    if not issubclass(sender, Stream2Mixin):
        return

    print 'Deleting Stream2 for: <%s: %s>' % (sender.__name__, instance)
    # GenericRelation in Stream2Mixin makes sure that Stream2 is being deleted when deleting the instance itself
    # so no need for us to explicitly do that
    # instance.stream2.delete()


class Listen(UUIDModel):
    listener = models.ForeignKey(AUTH_USER_MODEL)
    stream = models.ForeignKey('shoutit.Stream2')
    date_listened = models.DateTimeField(auto_now_add=True)

    class Meta(UUIDModel.Meta):
        unique_together = ('listener', 'stream')  # so the user can follow the stream only once

