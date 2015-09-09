# -*- coding: utf-8 -*-
"""

"""
from __future__ import unicode_literals

from django.conf import settings
from django.contrib.contenttypes.fields import GenericRelation
from django.db import models
from shoutit.models import UUIDModel
from django_pgjson.fields import JsonField
from shoutit.models.base import AttachedObjectMixin
from shoutit_crm.constants import CRMSourceType, XMLLinkCRMSourceStatus


class CRMProvider(UUIDModel):
    name = models.CharField(max_length=100)

    def __unicode__(self):
        return self.name


class CRMSource(UUIDModel):
    provider = models.ForeignKey('shoutit_crm.CRMProvider', related_name='%(class)s_set')
    type = models.PositiveSmallIntegerField(choices=CRMSourceType.choices)
    status = models.PositiveSmallIntegerField(choices=XMLLinkCRMSourceStatus.choices)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='%(class)s_set')

    class Meta(UUIDModel.Meta):
        abstract = True


class XMLLinkCRMSource(CRMSource):
    url = models.URLField()
    mapping = JsonField(blank=False)

    crm_shouts = GenericRelation('shoutit_crm.XMLCRMShout', related_query_name='xml_link_crm_source')

    def __unicode__(self):
        return "%s: %s @ %s" %(self.pk, self.url, unicode(self.provider))


class CRMShout(UUIDModel, AttachedObjectMixin):
    id_on_source = models.CharField(max_length=100)
    shout = models.ForeignKey('shoutit.Shout', related_name='crm_shout')

    class Meta(UUIDModel.Meta):
        abstract = True
        unique_together = ('content_type', 'object_id', 'id_on_source')

    @property
    def source(self):
        return self.attached_object


class XMLCRMShout(CRMShout):
    xml_data = models.TextField(blank=False)
