from __future__ import unicode_literals
from django.contrib import admin
from shoutit.admin_utils import UserLinkMixin
from shoutit_crm.models import CRMProvider, XMLLinkCRMSource, XMLCRMShout


@admin.register(CRMProvider)
class CRMProvider(admin.ModelAdmin):
    list_display = ('id', 'name', 'created_at')


@admin.register(XMLLinkCRMSource)
class XMLLinkCRMSourceAdmin(admin.ModelAdmin, UserLinkMixin):
    list_display = ('id', 'provider', '_user', 'url', 'status', 'created_at')
    raw_id_fields = ('provider', 'user')


@admin.register(XMLCRMShout)
class XMLCRMShoutAdmin(admin.ModelAdmin):
    list_display = ('id', 'id_on_source', 'shout', 'created_at')
    raw_id_fields = ('shout',)
