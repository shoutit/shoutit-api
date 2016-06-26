from __future__ import unicode_literals
import re
from collections import OrderedDict

from django.contrib.postgres.fields import ArrayField
from django.core import validators
from django.db import models
from hvad.models import TranslatedFields, TranslatableModel

from common.constants import TagValueType, TAG_TYPE_STR
from shoutit.settings import AUTH_USER_MODEL
from shoutit.models.base import UUIDModel, APIModelMixin, NamedLocationMixin, TranslatedModelFallbackMixin
from shoutit.models.listen import Listen2


class ShoutitSlugField(models.CharField):
    description = "Slug (up to %(max_length)s)"
    default_validators = [
        validators.MinLengthValidator(1),
        validators.RegexValidator(re.compile('^[-a-z0-9_]+$'),
                                  "Enter a valid 'slug' consisting of small letters, numbers, underscores or hyphens",
                                  'invalid')
    ]

    def __init__(self, *args, **kwargs):
        max_length = kwargs.get('max_length', 30)
        kwargs['max_length'] = max_length
        help_text = "Required. 1 to %s characters and can only contain small letters, numbers, underscores or hyphens" % max_length
        kwargs['help_text'] = kwargs.get('help_text', help_text)
        # Set db_index=True unless it's been set manually.
        if 'db_index' not in kwargs:
            kwargs['db_index'] = True
        super(ShoutitSlugField, self).__init__(*args, **kwargs)

    def deconstruct(self):
        name, path, args, kwargs = super(ShoutitSlugField, self).deconstruct()
        if kwargs.get("max_length", None) == 30:
            del kwargs['max_length']
        if self.db_index is False:
            kwargs['db_index'] = False
        else:
            del kwargs['db_index']
        return name, path, args, kwargs

    # todo: clean the field before saving


class Tag(APIModelMixin, TranslatedModelFallbackMixin, TranslatableModel, UUIDModel):
    name = models.CharField(max_length=30, db_index=True)
    slug = ShoutitSlugField()
    key = models.ForeignKey('shoutit.TagKey', related_name='tags', null=True, blank=True)

    creator = models.ForeignKey(AUTH_USER_MODEL, related_name='TagsCreated', null=True, blank=True,
                                on_delete=models.SET_NULL)
    image = models.URLField(max_length=1024, blank=True, default='')
    definition = models.TextField(blank=True, max_length=512, default='New Tag!')

    translations = TranslatedFields(
        _local_name=models.CharField(max_length=30, blank=True, default='', db_index=True)
    )

    class Meta:
        unique_together = ('slug', 'key')

    def __unicode__(self):
        return "%s:%s" % (self.key, self.slug)

    @property
    def is_category(self):
        return Category.exists(main_tag=self)

    @property
    def listeners_count(self):
        listen_type, target = Listen2.listen_type_and_target_from_object(self)
        return Listen2.objects.filter(type=listen_type, target=target).count()


class TagKey(TranslatedModelFallbackMixin, TranslatableModel, UUIDModel):
    name = models.CharField(max_length=30, db_index=True)
    slug = ShoutitSlugField()
    values_type = models.PositiveSmallIntegerField(choices=TagValueType.choices, default=TAG_TYPE_STR.value)
    category = models.ForeignKey('shoutit.Category', related_name='tag_keys')
    definition = models.CharField(max_length=100, blank=True, default='')

    def __unicode__(self):
        return "%s" % self.slug

    translations = TranslatedFields(
        _local_name=models.CharField(max_length=30, blank=True, default='')
    )

    class Meta:
        unique_together = ['slug', 'category']


class Category(TranslatedModelFallbackMixin, TranslatableModel, UUIDModel):
    name = models.CharField(max_length=30, unique=True, db_index=True)
    slug = ShoutitSlugField(unique=True)
    main_tag = models.OneToOneField('shoutit.Tag', related_name='+', null=True, blank=True)
    tags = models.ManyToManyField('shoutit.Tag', blank=True, related_name='category')
    filters = ArrayField(ShoutitSlugField(), size=10, blank=True, default=list)
    icon = models.URLField(max_length=1024, blank=True, default='')

    translations = TranslatedFields(
        _local_name=models.CharField(max_length=30, blank=True, default='', db_index=True)
    )

    def __unicode__(self):
        return self.name

    @property
    def image(self):
        return self.main_tag.image

    @property
    def filter_objects(self):
        objects = []
        # Get all the tags in one call
        tags = Tag.objects.filter(key__in=self.filters).values('name', 'key')
        for cat_filter in self.filters:
            filter_tags = filter(lambda t: t['key'] == cat_filter, tags)
            filter_tag_names = map(lambda t: t['name'], filter_tags)
            values = map(lambda ftn: {'name': ftn.title(), 'slug': ftn}, filter_tag_names)
            values.sort(key=lambda v: v['name'])
            filter_object = OrderedDict()
            filter_object['name'] = cat_filter.title()
            filter_object['slug'] = cat_filter
            filter_object['values'] = values
            objects.append(filter_object)
        objects.sort(key=lambda e: e.get('name'))
        return objects


class FeaturedTag(UUIDModel, NamedLocationMixin):
    title = models.CharField(max_length=100)
    tag = models.ForeignKey('shoutit.Tag', related_name='featured_in')
    rank = models.PositiveSmallIntegerField(validators=[validators.MinValueValidator(1)])

    class Meta:
        unique_together = ('country', 'state', 'city', 'rank')

    def __unicode__(self):
        return "%s in %s, %s, %s" % (self.tag.name, self.city, self.state, self.country)
