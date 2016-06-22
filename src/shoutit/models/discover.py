"""

"""
from __future__ import unicode_literals

from django.contrib.postgres.fields import HStoreField
from django.db import models
from mptt.models import MPTTModel, TreeForeignKey

from shoutit.models.base import UUIDModel, CountriesField, APIModelMixin


class DiscoverItem(MPTTModel, UUIDModel, APIModelMixin):
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

    class Meta:
        unique_together = ('countries', 'position', 'parent')

    class MPTTMeta:
        order_insertion_by = ['position']

    def __unicode__(self):
        return "%s in %s" % (self.title, filter(None, self.countries))

    @property
    def parents(self):
        return self.get_ancestors()

    @property
    def children(self):
        return self.get_children()
