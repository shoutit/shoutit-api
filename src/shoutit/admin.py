from __future__ import unicode_literals

from django import forms
from django.conf.urls import url
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import UserChangeForm
from django.core.urlresolvers import reverse
from django.db import models
from django.utils.translation import ugettext_lazy as _
from django_mptt_admin.admin import DjangoMpttAdmin
from hvad.admin import TranslatableAdmin
from push_notifications.admin import DeviceAdmin as PushDeviceAdmin
from push_notifications.models import APNSDevice, GCMDevice

from common.constants import UserType
from shoutit.utils import url_with_querystring
from .admin_filters import (ShoutitDateFieldListFilter, UserEmailFilter, UserDeviceFilter, APIClientFilter,
                            PublishedOnFilter)
from .admin_forms import PushBroadcastForm, ItemForm, CategoryForm, ImageFileChangeForm
from .admin_utils import (UserLinkMixin, tag_link, user_link, reply_link, LocationMixin, item_link, LinksMixin, links)
from .models import *  # NOQA


@property
def admin_url(self):
    return reverse('admin:%s_%s_change' % (self._meta.app_label, self._meta.model_name), args=(self.pk,))


models.Model.add_to_class('admin_url', admin_url)


class CustomUserChangeForm(UserChangeForm):
    username = forms.RegexField(
        label=_("Username"), max_length=30, min_length=2, regex=r"^[0-9a-zA-Z.]{2,30}$",
        help_text=_(
            'Required. 2 to 30 characters and can only contain A-Z, a-z, 0-9, and periods (.)'),
        error_messages={
            'invalid': _("This value may only contain A-Z, a-z, 0-9, and periods (.)")})


# User
@admin.register(User)
class CustomUserAdmin(UserAdmin, LocationMixin, LinksMixin):
    save_on_top = True
    list_display = (
        'id', '_links', 'username', '_profile', 'email', 'first_name', 'last_name', 'api_clients',
        '_devices', '_messaging', '_location', 'is_active', 'is_activated', 'is_guest', 'last_login', 'created_at')
    list_per_page = 50
    fieldsets = (
        (None, {'fields': ('type', 'username', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name', 'email', '_profile')}),
        (_('Permissions'), {'fields': ('is_active', 'is_activated', 'is_staff', 'is_superuser',
                                       'is_test', 'is_guest', 'groups', 'user_permissions')}),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
        (_('Extra'), {'fields': ('_devices', '_messaging')}),
    )
    list_filter = (UserEmailFilter, APIClientFilter, ('created_at', ShoutitDateFieldListFilter),
                   UserDeviceFilter, 'is_activated', 'is_active', 'is_test', 'is_guest', 'is_staff', 'is_superuser')
    readonly_fields = ('type', '_devices', '_messaging', '_profile')
    ordering = ('-created_at',)
    form = CustomUserChangeForm

    def get_urls(self):
        return [url(r'^([-\w]+)/password/$',
                    self.admin_site.admin_view(self.user_change_password),
                    name='shoutit_user_password_change')
                ] + super(UserAdmin, self).get_urls()

    def _profile(self, obj):
        ut = UserType.values[obj.type]
        return '<a href="%s">%s</a>' % (reverse('admin:shoutit_%s_change' % ut.lower(), args=(obj.ap.pk,)), ut)

    _profile.allow_tags = True
    _profile.short_description = 'Profile / Page'

    def _messaging(self, user):
        conversations_url = '<a href="%s">Conversations</a>'
        conversations_url %= url_with_querystring(reverse('admin:shoutit_conversation_changelist'), users=user.pk)
        messages_url = '<a href="%s">Messages</a>'
        messages_url %= url_with_querystring(reverse('admin:shoutit_message_changelist'), user=user.pk)
        return conversations_url + '<br/>' + messages_url

    _messaging.allow_tags = True
    _messaging.short_description = 'Messaging'

    def _devices(self, user):
        devices = ''
        for device in user.devices.all():
            devices += '<a href="%s">%s</a><br/>' % (device.admin_url, unicode(device))
        return devices

    _devices.allow_tags = True
    _devices.short_description = 'Devices'

    def api_clients(self, user):
        clients = ''
        for at in user.accesstoken_set.all():
            clients += '<a href="%s">%s</a><br/>' % (at.admin_url, unicode(at.client.name))
        return clients

    api_clients.allow_tags = True
    api_clients.short_description = 'Devices'

    def save_model(self, request, obj, form, change):
        update_fields = form.changed_data
        if isinstance(update_fields, list) and 'email' in update_fields:
            update_fields.append('is_activated')
        obj.save(update_fields=update_fields)


# Profile
@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin, UserLinkMixin):
    list_display = ('id', '_user', 'country', 'city', 'gender', 'image', 'mobile', 'created_at')
    search_fields = ['user__first_name', 'user__last_name', 'user__username', 'user__email', 'bio']
    readonly_fields = ('video', '_user')
    exclude = ('user',)
    list_filter = ('country', 'city', 'gender', UserEmailFilter, ('created_at', ShoutitDateFieldListFilter))
    ordering = ('-created_at',)


# Page
@admin.register(Page)
class ShoutitPageAdmin(admin.ModelAdmin, UserLinkMixin):
    list_display = ('id', '_user', 'name', 'creator', 'category', 'country', 'city', 'created_at')
    raw_id_fields = ('user', 'creator')
    search_fields = ('name', 'user__email')
    readonly_fields = ('video', '_user')
    exclude = ('user',)
    list_filter = ('country', 'city', 'category', ('created_at', ShoutitDateFieldListFilter))
    ordering = ('-created_at',)


# PageAdmin
@admin.register(PageAdmin)
class PageAdminAdmin(admin.ModelAdmin):
    list_display = ('page', 'admin', 'type')
    raw_id_fields = ('page', 'admin')


# PageCategory
@admin.register(PageCategory)
class PageCategoryAdmin(TranslatableAdmin, DjangoMpttAdmin):
    tree_auto_open = False
    form = ImageFileChangeForm


# LinkedFacebookAccount
@admin.register(LinkedFacebookAccount)
class LinkedFacebookAccountAdmin(admin.ModelAdmin, UserLinkMixin):
    list_display = ('id', '_user', 'facebook_id', 'access_token', 'scopes', 'expires_at', 'created_at')
    search_fields = ('user__first_name', 'user__last_name', 'user__username', 'user__email', 'facebook_id')
    ordering = ('-created_at',)
    readonly_fields = ('_user',)
    exclude = ('user',)


# LinkedGoogleAccount
@admin.register(LinkedGoogleAccount)
class LinkedGoogleAccountAdmin(admin.ModelAdmin, UserLinkMixin):
    list_display = ('id', '_user', 'gplus_id', 'created_at')
    search_fields = ('user__first_name', 'user__last_name', 'user__username', 'user__email', 'gplus_id')
    ordering = ('-created_at',)
    readonly_fields = ('_user',)
    exclude = ('user',)


# ProfileContact
@admin.register(ProfileContact)
class ProfileContactAdmin(admin.ModelAdmin, UserLinkMixin):
    list_display = ('id', '_user', 'first_name', 'last_name', 'emails', 'mobiles', 'created_at')
    search_fields = ('first_name', 'last_name', 'mobiles', 'emails')
    ordering = ('-created_at',)
    readonly_fields = ('_user',)
    exclude = ('user',)


# Item
@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    form = ItemForm
    list_display = ('id', 'name', 'price', 'currency', 'state', 'created_at')
    list_filter = ('currency', 'state', ('created_at', ShoutitDateFieldListFilter))
    raw_id_fields = ('videos',)
    ordering = ('-created_at',)


# Shout
@admin.register(Shout)
class ShoutAdmin(admin.ModelAdmin, UserLinkMixin, LocationMixin, LinksMixin):
    list_display = ('id', '_links', '_user', 'type', 'category', '_item', '_location', 'is_sss', 'is_disabled',
                    'priority', 'published_on', 'published_at', 'is_indexed')
    list_filter = ('type', 'category', 'is_sss', 'is_disabled', 'country', 'state', 'city', PublishedOnFilter,
                   ('created_at', ShoutitDateFieldListFilter), 'is_indexed')
    raw_id_fields = ('user', 'page_admin_user')
    exclude = ('item',)
    readonly_fields = ('_user', '_item')
    ordering = ('-published_at',)

    def _item(self, obj):
        return item_link(obj.item)

    _item.allow_tags = True
    _item.short_description = 'Item'


# Tag
@admin.register(Tag)
class TagAdmin(LinksMixin, TranslatableAdmin):
    list_display = ('name', 'slug', 'key', 'image', '_links')
    search_fields = ('name',)
    raw_id_fields = ('creator',)
    form = ImageFileChangeForm


# TagKey
@admin.register(TagKey)
class TagKeyAdmin(TranslatableAdmin):
    list_display = ('category', 'name', 'slug', 'values_type')
    search_fields = ('key',)
    list_filter = ('category', 'values_type')


# Category
@admin.register(Category)
class CategoryAdmin(TranslatableAdmin):
    list_display = ('name', 'slug', '_main_tag', 'filters', 'image', 'icon')
    raw_id_fields = ('main_tag', 'tags')
    ordering = ('name',)
    form = CategoryForm

    def _main_tag(self, category):
        return tag_link(category.main_tag)

    _main_tag.allow_tags = True
    _main_tag.short_description = 'Main Tag'


# FeaturedTag
@admin.register(FeaturedTag)
class FeaturedTagAdmin(admin.ModelAdmin):
    list_display = ('title', '_tag', 'country', 'state', 'city', 'rank')
    list_filter = ('country', 'state', 'city')
    ordering = ('country', 'state', 'city', 'rank')
    search_fields = ('title', 'tag__name', 'country', 'state', 'city')
    raw_id_fields = ('tag',)
    readonly_fields = ('_tag',)
    exclude = ('postal_code',)

    def _tag(self, f_tag):
        return tag_link(f_tag.tag)

    _tag.allow_tags = True
    _tag.short_description = 'Tag'


# DiscoverItem
@admin.register(DiscoverItem)
class DiscoverItemAdmin(TranslatableAdmin, DjangoMpttAdmin):
    tree_auto_open = False
    form = ImageFileChangeForm


# Conversation
@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ('id', '_web_url', 'type', 'country', '_users', '_messages', 'modified_at', 'created_at')
    readonly_fields = ('_last_message', '_attached_object', '_messages', '_web_url')
    fieldsets = (
        (None, {'fields': ('type', 'subject', 'icon', '_web_url')}),
        (_('Users'), {'fields': ('creator', 'users', 'admins', 'blocked')}),
        (_('Extra'), {'fields': ('_attached_object', '_last_message', '_messages')}),
    )
    raw_id_fields = ('users', 'creator')
    list_filter = ('type', 'country', ('created_at', ShoutitDateFieldListFilter),)
    ordering = ('-created_at',)

    def _users(self, conversation):
        def user_line(u):
            return '- %s | %s' % (user_link(u), reply_link(conversation, u))

        return '<br/>'.join([user_line(user) for user in conversation.users.all()])

    _users.short_description = 'Users'
    _users.allow_tags = True

    def _messages(self, conversation):
        messages_url = '<a href="%s">Messages [%s]</a>'
        messages = reverse('admin:shoutit_message_changelist')
        messages_url %= url_with_querystring(messages, conversation__id=conversation.pk), conversation.messages_count
        return messages_url

    _messages.allow_tags = True
    _messages.short_description = 'Messages'

    def _attached_object(self, instance):
        if not instance.attached_object:
            return ''
        return '<a href="%s">%s</a>' % (instance.attached_object.admin_url, unicode(instance.attached_object))

    _attached_object.allow_tags = True
    _attached_object.short_description = 'About'

    def _last_message(self, instance):
        if not instance.last_message:
            return ''
        return '<a href="%s">%s</a>' % (instance.last_message.admin_url, unicode(instance.last_message))

    _last_message.allow_tags = True
    _last_message.short_description = 'Last Message'

    def _web_url(self, instance):
        return links(instance)

    _web_url.allow_tags = True
    _web_url.short_description = 'Web url'


# Message
@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('id', '_conversation', '_user', 'summary', 'has_attachments', 'created_at')
    search_fields = ('user__id', 'user__username', 'text')
    readonly_fields = ('_conversation', '_user')
    raw_id_fields = ('conversation', 'user')
    fieldsets = (
        (None, {'fields': ('conversation', '_conversation', 'user', '_user', 'text')}),
    )
    ordering = ('-created_at',)

    def _user(self, message):
        return user_link(message.user)

    _user.allow_tags = True
    _user.short_description = 'User'

    def _conversation(self, message):
        conversation_link = reverse('admin:shoutit_conversation_change', args=(message.conversation.pk,))
        return '<a href="%s">%s</a>' % (conversation_link, message.conversation.pk)

    _conversation.allow_tags = True
    _conversation.short_description = 'Conversation'

    def has_attachments(self, message):
        return message.has_attachments

    has_attachments.boolean = True


# Message Attachment
@admin.register(MessageAttachment)
class MessageAttachmentAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'message', 'conversation', 'type', 'content_type', 'object_id', 'created_at')
    search_fields = ['message__id', 'conversation__id']
    ordering = ('-created_at',)


admin.site.register(ConversationDelete)
admin.site.register(MessageRead)
admin.site.register(MessageDelete)


# PushBroadcast
@admin.register(PushBroadcast)
class PushBroadcastAdmin(admin.ModelAdmin, UserLinkMixin):
    list_display = ('id', '_user', 'message', 'created_at')
    list_filter = (('created_at', ShoutitDateFieldListFilter),)
    readonly_fields = ('_user',)
    ordering = ('-created_at',)
    form = PushBroadcastForm

    def save_model(self, request, obj, form, change):
        obj.user = request.user
        obj.save()


# Django Push Notification
class CustomPushDeviceAdmin(PushDeviceAdmin, UserLinkMixin):
    list_display = ('__unicode__', '_device', 'device_id', '_user', 'active', 'date_created')
    search_fields = ('device_id', 'user__id', 'user__username')
    list_filter = ('active', ('date_created', ShoutitDateFieldListFilter))
    raw_id_fields = ('user',)
    readonly_fields = ('_device',)

    def _device(self, obj):
        device = obj.devices.first()
        if device:
            return '<a href="%s">Device</a>' % device.admin_url

    _device.allow_tags = True


admin.site.unregister(APNSDevice)
admin.site.register(APNSDevice, CustomPushDeviceAdmin)
admin.site.unregister(GCMDevice)
admin.site.register(GCMDevice, CustomPushDeviceAdmin)


# Device
@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    list_display = ('id', 'type', 'api_version', '_push_device')
    fieldsets = (
        (None, {'fields': ('type', 'api_version', '_push_device')}),
    )
    readonly_fields = ('type', '_push_device')
    list_filter = ('type', 'api_version')
    search_fields = ('apns_devices__user__id', 'apns_devices__user__username',
                     'gcm_devices__user__id', 'gcm_devices__user__username')

    def _push_device(self, obj):
        return '<a href="%s">%s</a>' % (obj.push_device.admin_url, unicode(obj.push_device))

    _push_device.allow_tags = True


# Video
@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    list_display = ('id', 'provider', 'link', 'duration', 'thumb', 'shout')
    list_filter = ('provider',)
    ordering = ('-created_at',)

    def link(self, obj):
        return '<a href="%s" about="_blank">%s</a>' % (obj.url, obj.id_on_provider)

    link.allow_tags = True

    def thumb(self, obj):
        return '<img src="%s" width="120"/>' % obj.thumbnail_url.replace('.jpg', '_small.jpg')

    thumb.allow_tags = True

    def shout(self, obj):
        try:
            _shout = obj.items.all()[0].shout
            _shout_admin_url = '<a href="%s">%s</a>' % (
                reverse('admin:shoutit_shout_change', args=(_shout.pk,)), _shout)
            _shout_web_url = links(_shout)
            return '%s | %s' % (_shout_admin_url, _shout_web_url)
        except:
            return 'None'

    shout.allow_tags = True


# Report
@admin.register(Report)
class ReportAdmin(admin.ModelAdmin, UserLinkMixin):
    list_display = ('id', 'type', '_user', 'text', 'attached_object', 'content_type',
                    'object_id', 'is_solved', 'is_disabled', 'created_at')
    list_filter = ('is_solved', 'is_disabled', ('created_at', ShoutitDateFieldListFilter))
    actions = ['mark_as_solved', 'mark_as_disabled']
    readonly_fields = ('_user', 'attached_object', 'content_type')
    raw_id_fields = ('user',)
    ordering = ('-created_at',)

    def mark_as_solved(self, request, queryset):
        queryset.update(is_solved=True)

    mark_as_solved.short_description = "Mark selected reports as solved"

    def mark_as_disabled(self, request, queryset):
        queryset.update(is_disabled=True)

    mark_as_disabled.short_description = "Mark selected reports as disabled"


# SMSInvitation
@admin.register(SMSInvitation)
class SMSInvitationAdmin(admin.ModelAdmin):
    list_display = ('id', 'status', 'country', 'mobile', 'user', 'created_at')
    list_filter = ('status', 'country', ('created_at', ShoutitDateFieldListFilter))
    search_fields = ('mobile', 'message')
    raw_id_fields = ('user',)
    ordering = ('-created_at',)


# ConfirmToken
@admin.register(ConfirmToken)
class ConfirmTokenAdmin(admin.ModelAdmin, UserLinkMixin):
    list_display = ('id', 'type', '_user', 'token', 'email', 'is_disabled', 'created_at')
    list_filter = ('type', 'is_disabled')
    ordering = ('-created_at',)
    readonly_fields = ('user',)


# GoogleLocation
@admin.register(GoogleLocation)
class GoogleLocationAdmin(admin.ModelAdmin):
    list_display = ('id', 'country', 'state', 'city', 'postal_code', 'latitude', 'longitude', 'is_indexed')
    list_filter = ('country', 'state', 'city', 'postal_code')


# PredefinedCity
@admin.register(PredefinedCity)
class PredefinedCity(admin.ModelAdmin):
    list_display = ('id', 'country', 'postal_code', 'state', 'city', 'latitude', 'longitude')


admin.site.register(Notification)
admin.site.register(Currency)
admin.site.register(SharedLocation)
admin.site.register(UserPermission)
admin.site.register(Permission)


@admin.register(DBUser)
class DBUserAdmin(admin.ModelAdmin, UserLinkMixin):
    list_display = ('id', '_user', 'db_link', 'shout', 'created_at')
    ordering = ('-created_at',)
    list_filter = (('created_at', ShoutitDateFieldListFilter),)
    readonly_fields = ('_user',)
    exclude = ('user',)


@admin.register(DBZ2User)
class DBZ2UserAdmin(admin.ModelAdmin, UserLinkMixin):
    list_display = ('id', '_user', 'db_link', 'shout', 'created_at')
    ordering = ('-created_at',)
    list_filter = (('created_at', ShoutitDateFieldListFilter),)
    readonly_fields = ('_user',)
    exclude = ('user',)


@admin.register(CLUser)
class CLUserAdmin(admin.ModelAdmin, UserLinkMixin):
    list_display = ('id', '_user', 'cl_email', 'shout', 'created_at')
    ordering = ('-created_at',)
    list_filter = (('created_at', ShoutitDateFieldListFilter),)
    readonly_fields = ('_user',)
    exclude = ('user',)


@admin.register(DBCLConversation)
class DBCLConversationAdmin(admin.ModelAdmin):
    list_display = ('id', 'in_email', '_from_user', '_to_user', 'shout', 'ref', 'sms_code', 'created_at')
    ordering = ('-created_at',)
    list_filter = (('created_at', ShoutitDateFieldListFilter),)
    exclude = ('from_user', 'to_user')
    readonly_fields = ('_from_user', '_to_user')

    def _from_user(self, obj):
        return user_link(obj.from_user)

    _from_user.allow_tags = True

    def _to_user(self, obj):
        return user_link(obj.to_user)

    _to_user.allow_tags = True
