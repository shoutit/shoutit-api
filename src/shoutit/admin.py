from __future__ import unicode_literals
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import UserChangeForm
from django import forms
from django.conf.urls import url
from django.core.urlresolvers import reverse
from django.db.models import Q

from shoutit.models import (
    User, Shout, Profile, Item, Tag, Notification, Category, Currency, Report, PredefinedCity,
    LinkedFacebookAccount, LinkedGoogleAccount, MessageAttachment, Post, SharedLocation, Video,
    Stream, Listen, UserPermission, Permission, Conversation, Message, MessageDelete, MessageRead,
    ConversationDelete, FeaturedTag, ConfirmToken, DBUser, CLUser, DBCLConversation)
from django.utils.translation import ugettext_lazy as _
# from shoutit.models import Business, BusinessConfirmation, BusinessCategory, StoredFile


# Shout
@admin.register(Shout)
class ShoutAdmin(admin.ModelAdmin):
    list_display = (
        'id', '_user', 'type', 'category', 'item', 'country', 'city', 'is_sss', 'is_disabled',
        'priority', 'date_published')
    list_filter = ('type', 'category', 'is_sss', 'is_disabled', 'country', 'city')
    readonly_fields = ('_user', 'item')
    ordering = ('-date_published',)

    def _user(self, obj):
        return user_link(obj.user)

    _user.allow_tags = True
    _user.short_description = 'User'


# Post
@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('id', '_user', 'type', 'text', 'country', 'city', 'muted', 'is_disabled')
    ordering = ('-created_at',)

    def _user(self, obj):
        return user_link(obj.user)

    _user.allow_tags = True
    _user.short_description = 'User'


admin.site.register(Item)


class UserEmailFilter(admin.SimpleListFilter):
    # Human-readable title which will be displayed in the
    # right admin sidebar just above the filter options.
    title = _('with email')

    # Parameter for the filter that will be used in the URL query.
    parameter_name = 'with_email'

    def lookups(self, request, model_admin):
        return (
            ('shoutit', _('only shoutit users')),
            ('yes', _('yes')),
            ('no', _('no')),
            ('cl', _('only cl users')),
        )

    def queryset(self, request, queryset):
        if queryset.model == User:
            if self.value() == 'shoutit':
                return queryset.filter(~Q(email=''), ~Q(email__icontains='@sale.craigslist.org'))
            if self.value() == 'yes':
                return queryset.filter(~Q(email=''))
            if self.value() == 'no':
                return queryset.filter(email='')
            if self.value() == 'cl':
                return queryset.filter(email__icontains='@sale.craigslist.org')
        elif queryset.model == Profile:
            if self.value() == 'shoutit':
                return queryset.filter(~Q(user__email=''), ~Q(user__email__icontains='@sale.craigslist.org'))
            if self.value() == 'yes':
                return queryset.filter(~Q(user__email=''))
            if self.value() == 'no':
                return queryset.filter(user__email='')
            if self.value() == 'cl':
                return queryset.filter(user__email__icontains='@sale.craigslist.org')


class CustomUserChangeForm(UserChangeForm):
    username = forms.RegexField(
        label=_("Username"), max_length=30, min_length=2, regex=r"^[0-9a-zA-Z.]{2,30}$",
        help_text=_(
            'Required. 2 to 30 characters and can only contain A-Z, a-z, 0-9, and periods (.)'),
        error_messages={
            'invalid': _("This value may only contain A-Z, a-z, 0-9, and periods (.)")})


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    save_on_top = True
    list_display = (
        'id', 'username', '_profile', 'email', 'first_name', 'last_name', '_messaging'
        , 'is_staff', 'is_test', 'is_superuser', 'is_active', 'is_activated', 'last_login')
    list_per_page = 50
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name', 'email', '_profile')}),
        (_('Permissions'), {'fields': ('is_active', 'is_activated', 'is_staff', 'is_superuser',
                                       'is_test', 'groups', 'user_permissions')}),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
        (_('Extra'), {'fields': ('_messaging',)}),
    )
    list_filter = ('is_active', 'is_activated', UserEmailFilter, 'is_test', 'is_staff',
                   'is_superuser', 'groups')
    readonly_fields = ('_messaging', '_profile')
    ordering = ('-date_joined',)
    form = CustomUserChangeForm

    def get_urls(self):
        return [url(r'^([-\w]+)/password/$',
                    self.admin_site.admin_view(self.user_change_password),
                    name='shoutit_user_password_change')
               ] + super(UserAdmin, self).get_urls()

    def _profile(self, obj):
        return '<a href="%s">Profile</a>' % (
            reverse('admin:shoutit_profile_change', args=(obj.profile.pk,)))

    _profile.allow_tags = True
    _profile.short_description = 'Profile'

    def _messaging(self, user):
        conversations = '<a href="%s">Conversations</a>' % (
            reverse('admin:shoutit_conversation_changelist')
            + '?users=' + user.pk)
        messages = '<a href="%s">Messages</a>' % (reverse('admin:shoutit_message_changelist')
                                                  + '?user=' + user.pk)
        return conversations + '<br/>' + messages

    _messaging.allow_tags = True
    _messaging.short_descriptions = 'Messaging'


# Profile
@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('id', '_user', 'country', 'city', 'gender', 'image', 'created_at')
    search_fields = ['user__first_name', 'user__last_name', 'user__username', 'user__email', 'bio']
    readonly_fields = ('_user',)
    list_filter = ('country', 'city', 'gender', UserEmailFilter)
    ordering = ('-created_at',)

    def _user(self, obj):
        return user_link(obj.user)

    _user.allow_tags = True
    _user.short_description = 'User'


@admin.register(LinkedFacebookAccount)
class LinkedFacebookAccountAdmin(admin.ModelAdmin):
    list_display = ('_user', 'facebook_id', 'access_token', 'expires', 'created_at')
    search_fields = ['user__first_name', 'user__last_name', 'user__username', 'user__email',
                     'facebook_id']
    ordering = ('-created_at',)

    def _user(self, obj):
        return user_link(obj.user)

    _user.allow_tags = True
    _user.short_description = 'User'


@admin.register(LinkedGoogleAccount)
class LinkedGoogleAccountAdmin(admin.ModelAdmin):
    list_display = ('_user', 'gplus_id', 'created_at')
    search_fields = ['user__first_name', 'user__last_name', 'user__username', 'user__email',
                     'facebook_id']
    ordering = ('-created_at',)

    def _user(self, obj):
        return user_link(obj.user)

    _user.allow_tags = True
    _user.short_description = 'User'


# # Business
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


# Tag
@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'stream')
    search_fields = ('name',)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    raw_id_fields = ('main_tag',)
    list_display = ('name', 'main_tag_name', 'tag_names')
    ordering = ('name',)
    filter_horizontal = ('tags',)

    def main_tag_name(self, category):
        return category.main_tag.name

    main_tag_name.short_description = 'Main Tag'

    def tag_names(self, category):
        return ', '.join([tag.name for tag in category.tags.all()])

    tag_names.short_description = 'Tags'


@admin.register(FeaturedTag)
class FeaturedTagAdmin(admin.ModelAdmin):
    raw_id_fields = ('tag',)
    list_display = ('tag_name', 'country', 'city', 'rank')
    list_filter = ('country', 'city')
    ordering = ('country', 'city', 'rank')
    search_fields = ('tag__name', 'tag__country', 'tag__city')

    def tag_name(self, featured_tag):
        return featured_tag.tag.name

    tag_name.short_description = 'Tag'


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ('id', 'type', '_users', '_messages', 'content_type', 'object_id', 'modified_at'
                    , 'created_at')
    readonly_fields = ('last_message', '_messages')
    fieldsets = (
        (None, {'fields': ('content_type', 'object_id', 'type', 'users', 'last_message')}),
        (_('Extra'), {'fields': ('_messages',)}),
    )
    raw_id_fields = ('users',)
    ordering = ('-created_at',)

    def _users(self, conversation):
        return '<br/>'.join(['- ' + user_link(user) for user in conversation.users.all()])

    _users.short_description = 'Users'
    _users.allow_tags = True

    def _messages(self, conversation):
        return '<a href="%s">Messages</a>' % (reverse('admin:shoutit_message_changelist')
                                              + '?conversation__id=' + conversation.pk)

    _messages.allow_tags = True
    _messages.short_description = 'Messages'


admin.site.register(ConversationDelete)


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('id', '_conversation', '_user', 'summary', 'has_attachments', 'created_at')
    readonly_fields = ('_conversation', '_user')
    fieldsets = (
        (None, {'fields': ('_conversation', '_user', 'text')}),
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
        return message.attachments.exists()

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
class ReportAdmin(admin.ModelAdmin):
    list_display = (
        'type_name', '_user', 'text', 'attached_object', 'content_type', 'object_id', 'is_solved',
        'is_disabled', 'created_at')
    list_filter = ('is_solved', 'is_disabled')
    actions = ['mark_as_solved', 'mark_as_disabled']
    readonly_fields = ('_user', 'attached_object', 'content_type')
    ordering = ('-created_at',)

    def mark_as_solved(self, request, queryset):
        queryset.update(is_solved=True)

    mark_as_solved.short_description = "Mark selected reports as solved"

    def mark_as_disabled(self, request, queryset):
        queryset.update(is_disabled=True)

    mark_as_disabled.short_description = "Mark selected reports as disabled"

    def _user(self, obj):
        return user_link(obj.user)

    _user.allow_tags = True
    _user.short_description = 'User'


@admin.register(ConfirmToken)
class ConfirmTokenAdmin(admin.ModelAdmin):
    list_display = ('id', 'type', '_user', 'token', 'email', 'is_disabled', 'created_at')
    list_filter = ('type', 'is_disabled')
    ordering = ('-created_at',)

    def _user(self, obj):
        return user_link(obj.user)

    _user.allow_tags = True
    _user.short_description = 'User'


@admin.register(DBUser)
class DBUserAdmin(admin.ModelAdmin):
    list_display = ('id', '_user', 'db_link', 'created_at')
    ordering = ('-created_at',)

    def _user(self, obj):
        return user_link(obj.user)

    _user.allow_tags = True
    _user.short_description = 'User'


@admin.register(CLUser)
class CLUserAdmin(admin.ModelAdmin):
    list_display = ('id', '_user', 'cl_email', 'created_at')
    ordering = ('-created_at',)

    def _user(self, obj):
        return user_link(obj.user)

    _user.allow_tags = True
    _user.short_description = 'User'


@admin.register(DBCLConversation)
class DBCLConversationAdmin(admin.ModelAdmin):
    list_display = ('id', 'in_email', '_from_user', '_to_user', 'shout', 'ref', 'created_at')
    ordering = ('-created_at',)

    def _from_user(self, obj):
        return user_link(obj.from_user)
    _from_user.allow_tags = True

    def _to_user(self, obj):
        return user_link(obj.to_user)
    _to_user.allow_tags = True

# admin.site.register(StoredFile)
admin.site.register(Video)
admin.site.register(Stream)
admin.site.register(Listen)
admin.site.register(Notification)
admin.site.register(Currency)
admin.site.register(PredefinedCity)
admin.site.register(SharedLocation)
admin.site.register(UserPermission)
admin.site.register(Permission)


def user_link(user):
    if not user:
        return 'system'
    user_url = reverse('admin:shoutit_user_change', args=(user.pk,))
    return '<a href="%s">%s</a>' % (user_url, user.name_username)
