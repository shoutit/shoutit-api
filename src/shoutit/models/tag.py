from __future__ import unicode_literals

import re

from django.core import validators
from django.db import models
from hvad.models import TranslatedFields, TranslatableModel

from common.constants import TagValueType, TAG_TYPE_STR
from common.utils import process_tag
from shoutit.models.base import UUIDModel, APIModelMixin, NamedLocationMixin, TranslatedModelFallbackMixin
from shoutit.models.listen import Listen2
from shoutit.settings import AUTH_USER_MODEL


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

    def clean(self, value, model_instance):
        value = process_tag(value)
        return super(ShoutitSlugField, self).clean(value, model_instance)


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
    slug = ShoutitSlugField(unique=True)
    values_type = models.PositiveSmallIntegerField(choices=TagValueType.choices, default=TAG_TYPE_STR.value)
    definition = models.CharField(max_length=100, blank=True, default='')

    def __unicode__(self):
        return "%s" % self.slug

    translations = TranslatedFields(
        _local_name=models.CharField(max_length=30, blank=True, default='')
    )


class Category(TranslatedModelFallbackMixin, TranslatableModel, UUIDModel):
    name = models.CharField(max_length=30, unique=True)
    slug = ShoutitSlugField(unique=True)
    main_tag = models.OneToOneField('shoutit.Tag', null=True, blank=True)
    filters = models.ManyToManyField(TagKey, blank=True, related_name='categories')
    icon = models.URLField(max_length=1024, blank=True, default='')

    translations = TranslatedFields(
        _local_name=models.CharField(max_length=30, blank=True, default='', db_index=True)
    )

    def __unicode__(self):
        return self.name

    @property
    def image(self):
        return self.main_tag.image


class FeaturedTag(UUIDModel, NamedLocationMixin):
    title = models.CharField(max_length=100)
    tag = models.ForeignKey('shoutit.Tag', related_name='featured_in')
    rank = models.PositiveSmallIntegerField(validators=[validators.MinValueValidator(1)])

    class Meta:
        unique_together = ('country', 'state', 'city', 'rank')

    def __unicode__(self):
        return "%s in %s, %s, %s" % (self.tag.name, self.city, self.state, self.country)
