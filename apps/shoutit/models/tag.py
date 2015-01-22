from django.db import models
from apps.shoutit.models.base import UUIDModel
from apps.shoutit.models.stream import Stream2Mixin
from django.conf import settings
AUTH_USER_MODEL = getattr(settings, 'AUTH_USER_MODEL')


class Tag(UUIDModel, Stream2Mixin):
    Name = models.CharField(max_length=100, default='', unique=True, db_index=True)
    Creator = models.ForeignKey(AUTH_USER_MODEL, related_name='TagsCreated', null=True, on_delete=models.SET_NULL)
    Image = models.URLField(max_length=1024, null=True, default='/static/img/shout_tag.png')
    DateCreated = models.DateTimeField(auto_now_add=True)
    Parent = models.ForeignKey('shoutit.Tag', related_name='ChildTags', blank=True, null=True, db_index=True)

    # Category = models.ForeignKey('shoutit.Category', related_name='Tags', null= True, default=None, db_index=True)
    Stream = models.OneToOneField('shoutit.Stream', related_name='OwnerTag', null=True, db_index=True)
    Definition = models.TextField(null=True, max_length=512, default='New Tag!')

    def __unicode__(self):
        return unicode(self.pk) + ": " + self.Name

    @property
    def IsCategory(self):
        return True if Category.objects.get(TopTag=self) else False


class Category(UUIDModel):
    Name = models.CharField(max_length=100, default='', unique=True, db_index=True)
    DateCreated = models.DateTimeField(auto_now_add=True)
    TopTag = models.OneToOneField('shoutit.Tag', related_name='OwnerCategory', null=True)
    Tags = models.ManyToManyField('shoutit.Tag', related_name='Category')

    def __unicode__(self):
        return self.Name