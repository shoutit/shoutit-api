from __future__ import unicode_literals
import re
from django.contrib.contenttypes.fields import GenericRelation
from django.core import validators
from django.db import models
from shoutit.settings import AUTH_USER_MODEL
from shoutit.models.base import UUIDModel, APIModelMixin, NamedLocationMixin
from shoutit.models.stream import StreamMixin


class Tag(UUIDModel, StreamMixin, APIModelMixin):
    name = models.CharField(
        max_length=30, unique=True, db_index=True,
        help_text='Required. 2 to 30 characters and can only contain a-z, 0-9, and the dash (-)',
        validators=[
            validators.MinLengthValidator(2),
            validators.RegexValidator(re.compile('^[0-9a-z-]+$'), "Enter a valid tag.", 'invalid'),
        ])
    creator = models.ForeignKey(AUTH_USER_MODEL, related_name='TagsCreated', null=True,
                                blank=True, on_delete=models.SET_NULL)
    image = models.URLField(
        max_length=1024, blank=True, default='https://tag-image.static.shoutit.com/default.jpg')
    definition = models.TextField(null=True, blank=True, max_length=512, default='New Tag!')
    _stream = GenericRelation('shoutit.Stream', related_query_name='tag')

    def __unicode__(self):
        return unicode(self.pk) + ": " + self.name

    @property
    def is_category(self):
        return Category.objects.get(main_tag=self).exists()

    # todo: filter the name before saving


class Category(UUIDModel):
    name = models.CharField(max_length=100, unique=True, db_index=True)
    main_tag = models.OneToOneField('shoutit.Tag', related_name='+', null=True, blank=True)
    tags = models.ManyToManyField('shoutit.Tag', related_name='category')

    def __unicode__(self):
        return self.name


class FeaturedTag(UUIDModel, NamedLocationMixin):
    title = models.CharField(max_length=100)
    tag = models.ForeignKey('shoutit.Tag', related_name='featured_in')
    rank = models.PositiveSmallIntegerField(validators=[validators.MinValueValidator(1)])

    class Meta:
        unique_together = ('country', 'state', 'city', 'rank')

    def __unicode__(self):
        return "%s in %s, %s, %s" % (self.tag.name, self.city, self.state, self.country)