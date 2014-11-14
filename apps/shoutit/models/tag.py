from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.shoutit.models.stream import Stream, Stream2, Stream2Mixin


class Tag(models.Model, Stream2Mixin):
    class Meta:
        app_label = 'shoutit'

    def __unicode__(self):
        return unicode(self.id) + ": " + self.Name

    Name = models.CharField(max_length=100, default='', unique=True, db_index=True)
    Creator = models.ForeignKey(User, related_name='TagsCreated', null=True, on_delete=models.SET_NULL)
    Image = models.URLField(max_length=1024, null=True, default='/static/img/shout_tag.png')
    DateCreated = models.DateTimeField(auto_now_add=True)
    Parent = models.ForeignKey('Tag', related_name='ChildTags', blank=True, null=True, db_index=True)

    #	Category = models.ForeignKey(Category, related_name='Tags', null= True, default=None, db_index=True)
    Stream = models.OneToOneField(Stream, related_name='OwnerTag', null=True, db_index=True)
    Definition = models.TextField(null=True, max_length=512, default='New Tag!')

    @property
    def IsCategory(self):
        return True if Category.objects.get(TopTag=self) else False


@receiver(post_save, sender=Tag)
def attach_stream(sender, instance, created, raw, using, update_fields, **kwargs):

    # on new profile create stream2 and attach it
    if created:
        # creating the stream2
        stream2 = Stream2(owner=instance)
        stream2.save()


class Category(models.Model):
    class Meta:
        app_label = 'shoutit'

    def __unicode__(self):
        return self.Name

    Name = models.CharField(max_length=100, default='', unique=True, db_index=True)
    DateCreated = models.DateTimeField(auto_now_add=True)
    TopTag = models.OneToOneField(Tag, related_name='OwnerCategory', null=True)
    Tags = models.ManyToManyField(Tag, related_name='Category')
