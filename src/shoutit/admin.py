from __future__ import unicode_literals

import uuid

import boto
from django import forms
from django.conf import settings
from django.conf.urls import url
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import UserChangeForm
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _
from mptt.admin import MPTTModelAdmin
from push_notifications.admin import DeviceAdmin
from push_notifications.models import APNSDevice, GCMDevice

from common.constants import UserType
from shoutit.admin_filters import ShoutitDateFieldListFilter, UserEmailFilter, UserDeviceFilter, APIClientFilter, \
    PublishedOnFilter
from shoutit.admin_utils import (
    UserLinkMixin, tag_link, user_link, reply_link, LocationMixin, item_link, LinksMixin, links)
from shoutit.forms import PushBroadcastForm, ItemForm
from shoutit.models import (
    User, Shout, Profile, Item, Tag, Notification, Category, Currency, Report, PredefinedCity,
    LinkedFacebookAccount, LinkedGoogleAccount, MessageAttachment, Post, SharedLocation, Video,
    UserPermission, Permission, Conversation, Message, MessageDelete, MessageRead,
    ConversationDelete, FeaturedTag, ConfirmToken, DBUser, CLUser, DBCLConversation, DBZ2User, SMSInvitation,
    PushBroadcast, GoogleLocation, Page, PageCategory, PageAdmin, DiscoverItem, TagKey)
from shoutit_pusher.models import PusherChannel, PusherChannelJoin


# from shoutit.models import Business, BusinessConfirmation, BusinessCategory, StoredFile


# Shout
@admin.register(Shout)
class ShoutAdmin(admin.ModelAdmin, UserLinkMixin, LocationMixin, LinksMixin):
    list_display = ('id', '_links', '_user', 'type', 'category', '_item', '_location', 'is_sss', 'is_disabled',
                    'priority', 'published_on', 'date_published')
    list_filter = ('type', 'category', 'is_sss', 'is_disabled', 'country', 'city', PublishedOnFilter,
                   ('created_at', ShoutitDateFieldListFilter))
    raw_id_fields = ('user', 'page_admin_user')
    exclude = ('item',)
    readonly_fields = ('_user', '_item')
    ordering = ('-date_published',)

    def _item(self, obj):
        return item_link(obj.item)

    _item.allow_tags = True
    _item.short_description = 'Item'


# Post
@admin.register(Post)
class PostAdmin(admin.ModelAdmin, UserLinkMixin, LocationMixin):
    list_display = ('id', '_user', 'type', 'text', '_location', 'muted', 'is_disabled')
    ordering = ('-created_at',)
    list_filter = ('type', 'is_disabled', 'country', 'city', ('created_at', ShoutitDateFieldListFilter))
    raw_id_fields = ('user', 'page_admin_user')


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    form = ItemForm


class CustomUserChangeForm(UserChangeForm):
    username = forms.RegexField(
        label=_("Username"), max_length=30, min_length=2, regex=r"^[0-9a-zA-Z.]{2,30}$",
        help_text=_(
            'Required. 2 to 30 characters and can only contain A-Z, a-z, 0-9, and periods (.)'),
        error_messages={
            'invalid': _("This value may only contain A-Z, a-z, 0-9, and periods (.)")})


@admin.register(User)
class CustomUserAdmin(UserAdmin, LocationMixin, LinksMixin):
    save_on_top = True
    list_display = (
        'id', '_links', 'username', '_profile', 'email', 'first_name', 'last_name', 'api_client_name',
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
        conversations = '<a href="%s">Conversations</a>' % (
            reverse('admin:shoutit_conversation_changelist') + '?users=' + user.pk)
        messages = '<a href="%s">Messages</a>' % (reverse('admin:shoutit_message_changelist') + '?user=' + user.pk)
        return conversations + '<br/>' + messages

    _messaging.allow_tags = True
    _messaging.short_description = 'Messaging'

    def _devices(self, user):
        apns_device = ''
        if user.apns_device:
            apns_device = '<a href="%s">iPhone</a>' % (
                reverse('admin:push_notifications_apnsdevice_change', args=[user.apns_device.id]))
        gcm_device = ''
        if user.gcm_device:
            gcm_device = '<a href="%s">Android</a>' % (
                reverse('admin:push_notifications_gcmdevice_change', args=[user.gcm_device.id]))
        return ((apns_device + '<br/>') if apns_device else '') + gcm_device

    _devices.allow_tags = True
    _devices.short_description = 'Devices'

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


@admin.register(LinkedFacebookAccount)
class LinkedFacebookAccountAdmin(admin.ModelAdmin, UserLinkMixin):
    list_display = ('id', '_user', 'facebook_id', 'access_token', 'scopes', 'expires_at', 'created_at')
    search_fields = ('user__first_name', 'user__last_name', 'user__username', 'user__email', 'facebook_id')
    ordering = ('-created_at',)
    readonly_fields = ('_user',)
    exclude = ('user',)


@admin.register(LinkedGoogleAccount)
class LinkedGoogleAccountAdmin(admin.ModelAdmin, UserLinkMixin):
    list_display = ('id', '_user', 'gplus_id', 'created_at')
    search_fields = ('user__first_name', 'user__last_name', 'user__username', 'user__email', 'gplus_id')
    ordering = ('-created_at',)
    readonly_fields = ('_user',)
    exclude = ('user',)


class TagChangeForm(forms.ModelForm):
    image_file = forms.FileField(required=False)

    class Meta:
        model = Tag
        fields = '__all__'

    def clean_image_file(self):
        image_file = self.cleaned_data.get('image_file')
        if not image_file:
            return
        s3 = boto.connect_s3(settings.AWS_ACCESS_KEY_ID, settings.AWS_SECRET_ACCESS_KEY)
        bucket = s3.get_bucket('shoutit-tag-image-original')
        filename = "%s-%s.jpg" % (uuid.uuid4(), self.cleaned_data['name'])
        key = bucket.new_key(filename)
        key.set_metadata('Content-Type', 'image/jpg')
        key.set_contents_from_file(image_file)
        s3_image_url = 'https://tag-image.static.shoutit.com/%s' % filename
        self.cleaned_data['image'] = s3_image_url


# Tag
@admin.register(Tag)
class TagAdmin(admin.ModelAdmin, LinksMixin):
    list_display = ('name', 'image', '_links')
    search_fields = ('name',)
    raw_id_fields = ('creator',)
    form = TagChangeForm


@admin.register(TagKey)
class TagKeyAdmin(admin.ModelAdmin):
    list_display = ('key', 'values_type')
    search_fields = ('key',)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    raw_id_fields = ('main_tag',)
    list_display = ('name', '_main_tag', 'tag_names')
    ordering = ('name',)
    filter_horizontal = ('tags',)

    def _main_tag(self, category):
        return tag_link(category.main_tag)

    _main_tag.allow_tags = True
    _main_tag.short_description = 'Main Tag'

    def tag_names(self, category):
        return ', '.join([tag.name for tag in category.tags.all()])

    tag_names.short_description = 'Tags'


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


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ('id', 'type', '_users', '_messages', 'content_type', 'object_id', 'modified_at',
                    'created_at')
    readonly_fields = ('last_message', '_messages')
    fieldsets = (
        (None, {'fields': ('content_type', 'object_id', 'type', 'users', 'last_message')}),
        (_('Extra'), {'fields': ('_messages',)}),
    )
    raw_id_fields = ('users',)
    list_filter = (('created_at', ShoutitDateFieldListFilter),)
    ordering = ('-created_at',)

    def _users(self, conversation):
        def user_line(u):
            return '- %s | %s' % (user_link(u), reply_link(conversation, u))

        return '<br/>'.join([user_line(user) for user in conversation.users.all()])

    _users.short_description = 'Users'
    _users.allow_tags = True

    def _messages(self, conversation):
        return '<a href="%s">Messages [%s]</a>' % (
            reverse('admin:shoutit_message_changelist') + '?conversation__id=' + conversation.pk,
            conversation.messages_count)

    _messages.allow_tags = True
    _messages.short_description = 'Messages'


admin.site.register(ConversationDelete)


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
        conversation_link = reverse('admin:shoutit_conversation_change',
                                    args=(message.conversation.pk,))
        return '<a href="%s">%s</a>' % (conversation_link, message.conversation.pk)

    _conversation.allow_tags = True
    _conversation.short_description = 'Conversation'

    def has_attachments(self, message):
        return message.has_attachments

    has_attachments.boolean = True


admin.site.register(MessageRead)
admin.site.register(MessageDelete)


# Message Attachment
@admin.register(MessageAttachment)
class MessageAttachmentAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'message', 'conversation', 'type', 'content_type', 'object_id', 'created_at')
    search_fields = ['message__id', 'conversation__id']
    ordering = ('-created_at',)


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


@admin.register(ConfirmToken)
class ConfirmTokenAdmin(admin.ModelAdmin, UserLinkMixin):
    list_display = ('id', 'type', '_user', 'token', 'email', 'is_disabled', 'created_at')
    list_filter = ('type', 'is_disabled')
    ordering = ('-created_at',)
    readonly_fields = ('user',)


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


@admin.register(PredefinedCity)
class PredefinedCity(admin.ModelAdmin):
    list_display = ('id', 'country', 'postal_code', 'state', 'city', 'latitude', 'longitude')


# Django Push Notification
class CustomDeviceAdmin(DeviceAdmin, UserLinkMixin):
    list_display = ('__unicode__', 'device_id', '_user', 'active', 'date_created')
    search_fields = ('device_id', 'user__id', 'user__username')
    list_filter = ('active', ('date_created', ShoutitDateFieldListFilter))
    raw_id_fields = ('user',)


admin.site.unregister(APNSDevice)
admin.site.register(APNSDevice, CustomDeviceAdmin)
admin.site.unregister(GCMDevice)
admin.site.register(GCMDevice, CustomDeviceAdmin)


# Pusher
@admin.register(PusherChannel)
class PusherChannelAdmin(admin.ModelAdmin):
    list_display = ('type', 'name')
    raw_id_fields = ('users',)


@admin.register(PusherChannelJoin)
class PusherChannelJoinAdmin(admin.ModelAdmin):
    list_display = ('channel', 'user')
    raw_id_fields = ('channel', 'user')


@admin.register(SMSInvitation)
class SMSInvitationAdmin(admin.ModelAdmin):
    list_display = ('id', 'status', 'country', 'mobile', 'user', 'created_at')
    list_filter = ('status', 'country', ('created_at', ShoutitDateFieldListFilter))
    search_fields = ('mobile', 'message')
    raw_id_fields = ('user',)
    ordering = ('-created_at',)


@admin.register(GoogleLocation)
class GoogleLocationAdmin(admin.ModelAdmin):
    list_display = ('id', 'country', 'state', 'city', 'postal_code', 'latitude', 'longitude')
    list_filter = ('country', 'state', 'city', 'postal_code')


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


@admin.register(Page)
class ShoutitPageAdmin(admin.ModelAdmin, UserLinkMixin):
    list_display = ('id', '_user', 'name', 'creator', 'category', 'country', 'city', 'created_at')
    raw_id_fields = ('user', 'creator')
    search_fields = ('name', 'user__email')
    readonly_fields = ('video', '_user')
    exclude = ('user',)
    list_filter = ('country', 'city', 'category', ('created_at', ShoutitDateFieldListFilter))
    ordering = ('-created_at',)


@admin.register(PageAdmin)
class PageAdminAdmin(admin.ModelAdmin):
    list_display = ('page', 'admin', 'type')
    raw_id_fields = ('page', 'admin')


@admin.register(PageCategory)
class PageCategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'slug', 'parent')
    list_filter = ('parent',)


@admin.register(DiscoverItem)
class DiscoverItemAdmin(MPTTModelAdmin):
    mptt_level_indent = 20
    mptt_indent_field = "some_node_field"


# Others
admin.site.register(Notification)
admin.site.register(Currency)
admin.site.register(SharedLocation)
admin.site.register(UserPermission)
admin.site.register(Permission)


# # Business
# admin.site.register(StoredFile)
# @admin.register(Business)
# class BusinessProfileAdmin(admin.ModelAdmin):
# list_display = ('id', 'name', 'user', 'country', 'city', 'Category', 'Confirmed')
# search_fields = ['name', 'user__email', 'Website']
# readonly_fields = ('user', 'LastToken')


# BusinessCreateApplication
# class BusinessCreateApplicationAdmin(admin.ModelAdmin):
# list_display = ('name', 'user', 'Business','confirmation_url','country', 'city', 'Status')
# search_fields = ['name', 'user__email','Website', 'Phone']
# readonly_fields = ('user','Business','LastToken')
# list_filter = ('Status',)
# actions = ['accept_business', 'reject_business']
#
# def confirmation_url(self, obj):
# try:
# confirmation = obj.user.BusinessConfirmations.all().order_by('id')[0]
# return '<a href="%s%s">%s</a>' % ('/admin/ShoutWebsite/businessconfirmation/', confirmation.pk, obj.user)
#         except :
#             return 'Docs not yet submitted'
#
#     confirmation_url.allow_tags = True
#     confirmation_url.short_description = 'Confirmation Link'
#
#     def accept_business(self, request, queryset):
#         for q in queryset:
#             business_controller.AcceptBusiness(request, q)
#     accept_business.short_description = "Accept selected business creation applications"
#
#     def reject_business(self, request, queryset):
#         pass
#     #TODO send email with explanation to user via email
#     reject_business.short_description = "Reject selected business creation applications"
# admin.site.register(BusinessCreateApplication, BusinessCreateApplicationAdmin)


# BusinessConfirmation
# class BusinessConfirmationAdmin(admin.ModelAdmin):
#     list_display = ('id', 'user')
#
# admin.site.register(BusinessConfirmation, BusinessConfirmationAdmin)


# # BusinessCategory
# class BusinessCategoryAdmin(admin.ModelAdmin):
#     list_display = ('id', 'name', 'Source', 'SourceID', 'Parent')
#     search_fields = ['name', 'Parent__name']
#
# admin.site.register(BusinessCategory, BusinessCategoryAdmin)
