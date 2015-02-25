from django.contrib.contenttypes.fields import GenericRelation
from django.db import models
from django.conf import settings

from shoutit.models.base import UUIDModel, APIModelMixin
from shoutit.models.stream import Stream2Mixin, Listen

AUTH_USER_MODEL = getattr(settings, 'AUTH_USER_MODEL')


class Tag(UUIDModel, Stream2Mixin, APIModelMixin):
    name = models.CharField(max_length=100, default='', blank=True, unique=True, db_index=True)
    Creator = models.ForeignKey(AUTH_USER_MODEL, related_name='TagsCreated', null=True, blank=True, on_delete=models.SET_NULL)
    image = models.CharField(max_length=1024, null=True, blank=True, default='/static/img/shout_tag.png')
    DateCreated = models.DateTimeField(auto_now_add=True)
    Parent = models.ForeignKey('shoutit.Tag', related_name='ChildTags', null=True, blank=True, db_index=True)

    Stream = models.OneToOneField('shoutit.Stream', related_name='tag', null=True, blank=True, db_index=True)
    Definition = models.TextField(null=True, blank=True, max_length=512, default='New Tag!')

    _stream2 = GenericRelation('shoutit.Stream2', related_query_name='tag')

    def __unicode__(self):
        return unicode(self.pk) + ": " + self.name

    @property
    def IsCategory(self):
        return True if Category.objects.get(TopTag=self) else False

    @property
    def listeners_count(self):
        return self.stream2.listeners.count()


class Category(UUIDModel):
    name = models.CharField(max_length=100, default='', blank=True, unique=True, db_index=True)
    TopTag = models.OneToOneField('shoutit.Tag', related_name='OwnerCategory', null=True, blank=True)
    tags = models.ManyToManyField('shoutit.Tag', related_name='Category', null=True, blank=True)

    def __unicode__(self):
        return self.name