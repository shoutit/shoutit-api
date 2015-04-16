from __future__ import unicode_literals
import re
from django.contrib.contenttypes.fields import GenericRelation
from django.core import validators
from django.db import models
from django.conf import settings
from common.constants import DEFAULT_LOCATION

from shoutit.models.base import UUIDModel, APIModelMixin
from shoutit.models.stream import StreamMixin

AUTH_USER_MODEL = getattr(settings, 'AUTH_USER_MODEL')


class Tag(UUIDModel, StreamMixin, APIModelMixin):
    name = models.CharField(max_length=30, unique=True, db_index=True,
                            validators=[
                                validators.MinLengthValidator(2),
                                validators.RegexValidator(re.compile('[0-9a-z-]{2,30}'), "Enter a valid tag.", 'invalid'),
                            ])
    Creator = models.ForeignKey(AUTH_USER_MODEL, related_name='TagsCreated', null=True, blank=True, on_delete=models.SET_NULL)
    image = models.CharField(max_length=1024, null=True, blank=True)
    DateCreated = models.DateTimeField(auto_now_add=True)
    Parent = models.ForeignKey('shoutit.Tag', related_name='ChildTags', null=True, blank=True, db_index=True)

    Definition = models.TextField(null=True, blank=True, max_length=512, default='New Tag!')

    _stream = GenericRelation('shoutit.Stream', related_query_name='tag')

    def __str__(self):
        return unicode(self.pk) + ": " + self.name

    @property
    def is_category(self):
        return Category.objects.get(main_tag=self).exists()

    # todo: filter the name before saving


class Category(UUIDModel):
    name = models.CharField(max_length=100, unique=True, db_index=True)
    main_tag = models.OneToOneField('shoutit.Tag', related_name='+', null=True, blank=True)
    tags = models.ManyToManyField('shoutit.Tag', related_name='category')

    def __str__(self):
        return self.name


class FeaturedTag(UUIDModel):
    tag = models.ForeignKey('shoutit.Tag', related_name='featured_in')
    country = models.CharField(max_length=200, default=DEFAULT_LOCATION['country'], db_index=True)
    city = models.CharField(max_length=200, default=DEFAULT_LOCATION['city'], db_index=True)
    rank = models.PositiveSmallIntegerField(validators=[validators.MinValueValidator(1)])

    class Meta:
        unique_together = ('country', 'city', 'rank')
