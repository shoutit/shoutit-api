from __future__ import unicode_literals
import re
from django.core import validators
from django.db import models
from shoutit.settings import AUTH_USER_MODEL
from shoutit.models.base import UUIDModel, APIModelMixin, NamedLocationMixin
from shoutit.models.listen import Listen2


class TagNameField(models.CharField):
    description = "String from 2 to 30 characters and can only contain a-z, 0-9, and the dash (-)"

    def __init__(self, *args, **kwargs):
        kwargs['max_length'] = kwargs.get('max_length', 30)
        kwargs['unique'] = kwargs.get('unique', True)
        kwargs['db_index'] = kwargs.get('db_index', True)
        kwargs['help_text'] = kwargs.get('help_text', "Required. 2 to 30 characters and can only contain a-z, 0-9, and the dash (-)")
        kwargs['validators'] = kwargs.get('validators', [
            validators.MinLengthValidator(2),
            validators.RegexValidator(re.compile('^[0-9a-z-]+$'), "Enter a valid tag.", 'invalid'),
        ])
        super(TagNameField, self).__init__(*args, **kwargs)


class Tag(UUIDModel, APIModelMixin):
    name = TagNameField()
    creator = models.ForeignKey(AUTH_USER_MODEL, related_name='TagsCreated', null=True, blank=True,
                                on_delete=models.SET_NULL)
    image = models.URLField(max_length=1024, blank=True, default='https://tag-image.static.shoutit.com/default.jpg')
    definition = models.TextField(null=True, blank=True, max_length=512, default='New Tag!')

    def __unicode__(self):
        return "%s: %s" % (self.pk, self.name)

    @property
    def is_category(self):
        return Category.objects.get(main_tag=self).exists()

    @property
    def listeners_count(self):
        listen_type, target = Listen2.listen_type_and_target_from_object(self)
        return Listen2.objects.filter(type=listen_type, target=target).count()

    # todo: filter the name before saving


class Category(UUIDModel):
    name = models.CharField(max_length=100, unique=True, db_index=True)
    slug = TagNameField()
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
