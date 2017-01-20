"""

"""
from __future__ import unicode_literals

from django.contrib.postgres.fields import HStoreField
from django.db import models
from hvad.models import TranslatedFields, TranslatableModel
from mptt.models import MPTTModel, TreeForeignKey

from shoutit.models.base import (CountriesField, APIModelMixin, TranslationTreeManager, UUIDModel,
                                 TranslatedModelFallbackMixin)


class DiscoverItem(APIModelMixin, TranslatedModelFallbackMixin, TranslatableModel, MPTTModel, UUIDModel):
    title = models.CharField(max_length=100)
    subtitle = models.CharField(max_length=100, blank=True)
    description = models.CharField(max_length=100, blank=True)
    position = models.PositiveSmallIntegerField()
    countries = CountriesField()

    image = models.URLField(blank=True, default='')
    cover = models.URLField(blank=True, default='')
    icon = models.URLField(blank=True, default='')

    parent = TreeForeignKey('self', null=True, blank=True, related_name='children')
    show_children = models.BooleanField(default=True)
    shouts_query = HStoreField(blank=True)
    show_shouts = models.BooleanField(default=False)

    objects = TranslationTreeManager()

    class Meta:
        unique_together = ('countries', 'position', 'parent')

    # Todo (mo): Remove position, ordering can be done using mptt attrs
    class MPTTMeta:
        order_insertion_by = ['position']

    translations = TranslatedFields(
        _local_title=models.CharField(max_length=30, blank=True, default=''),
        _local_sub_title=models.CharField(max_length=60, blank=True, default=''),
        _local_description=models.CharField(max_length=100, blank=True, default='')
    )

    def __str__(self):
        return "%s in %s" % (self.title, [c for c in self.countries if c])

    @property
    def parents(self):
        return self.get_ancestors()

    @property
    def children(self):
        return self.get_children()
