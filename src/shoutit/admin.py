from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import UserChangeForm
from django import forms

from shoutit.models import User, Shout, Profile, Item,\
    Tag, Notification, Category, Currency, \
    Report, PredefinedCity, LinkedFacebookAccount, LinkedGoogleAccount, MessageAttachment, Post, SharedLocation, Video, Stream, \
    Listen, UserPermission, Permission, Conversation, Message, MessageDelete, MessageRead, ConversationDelete, FeaturedTag

from django.utils.translation import ugettext_lazy as _

# from shoutit.models import Business, BusinessConfirmation, BusinessCategory, StoredFile

# Shout
@admin.register(Shout)
class ShoutAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'owner', 'owner_profile', 'type', 'item', 'text', 'country', 'city', 'is_sss', 'is_disabled')
    list_filter = ('type', 'is_sss', 'is_disabled')
    readonly_fields = ('user', 'tags', 'item')

    def owner(self, obj):
        return '<a href="%s%s" target="_blank">%s</a> | <a href="/user/%s" target="_blank">link</a>' % (
            '/admin/auth/user/', obj.user.username, obj.user, obj.user.username)

    owner.allow_tags = True
    owner.short_description = 'User'

    def owner_profile(self, obj):
        if hasattr(obj.user, 'profile') and obj.user.profile:
            return '<a href="%s%s">%s</a>' % ('/admin/ShoutWebsite/userprofile/', obj.user.profile.pk, obj.user.profile)
        elif hasattr(obj.user, 'Business') and obj.user.Business:
            return '<a href="%s%s">%s</a>' % ('/admin/ShoutWebsite/businessprofile/', obj.user.Business.pk, obj.user.Business)

    owner_profile.allow_tags = True
    owner_profile.short_description = 'User Profile/Business'


# Post
class PostAdmin(admin.ModelAdmin):
    list_display = ('id',  'user', 'type', 'text', 'country', 'city', 'muted', 'is_disabled')

admin.site.register(Post, PostAdmin)
admin.site.register(Item)


class CustomUserChangeForm(UserChangeForm):
    username = forms.RegexField(
        label=_("Username"), max_length=30, min_length=2, regex=r"^[0-9a-zA-Z.]{2,30}$",
        help_text=_('Required. 2 to 30 characters and can only contain A-Z, a-z, 0-9, and periods (.)'),
        error_messages={
            'invalid': _("This value may only contain A-Z, a-z, 0-9, and periods (.)")})


class CustomUserAdmin(UserAdmin):
    save_on_top = True
    list_display = ('id', 'username', 'email', 'first_name', 'last_name', 'is_staff', 'last_login')
    list_per_page = 50

    form = CustomUserChangeForm

    def get_urls(self):
        from django.conf.urls import patterns
        return patterns('',
            (r'^([-\w]+)/password/$',
             self.admin_site.admin_view(self.user_change_password))
        ) + super(UserAdmin, self).get_urls()

admin.site.register(User, CustomUserAdmin)


# Profile
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'country', 'city', 'gender', 'image')
    search_fields = ['user__first_name', 'user__last_name', 'user__username', 'user__email', 'bio']
    readonly_fields = ('user',)
    list_filter = ('country', 'city', 'gender')

admin.site.register(Profile, ProfileAdmin)


class LinkedFacebookAccountAdmin(admin.ModelAdmin):
    list_display = ('user', 'facebook_id', 'access_token', 'expires')
    search_fields = ['user__first_name', 'user__last_name', 'user__username', 'user__email', 'facebook_id']

admin.site.register(LinkedFacebookAccount, LinkedFacebookAccountAdmin)


class LinkedGoogleAccountAdmin(admin.ModelAdmin):
    list_display = ('user', 'gplus_id')
    search_fields = ['user__first_name', 'user__last_name', 'user__username', 'user__email', 'facebook_id']

admin.site.register(LinkedGoogleAccount, LinkedGoogleAccountAdmin)


# # Business
# @admin.register(Business)
# class BusinessProfileAdmin(admin.ModelAdmin):
#     list_display = ('id', 'name', 'user', 'country', 'city', 'Category', 'Confirmed')
#     search_fields = ['name', 'user__email', 'Website']
#     readonly_fields = ('user', 'LastToken')


# BusinessCreateApplication
# class BusinessCreateApplicationAdmin(admin.ModelAdmin):
# list_display = ('name', 'user', 'Business','confirmation_url','country', 'city', 'Status')
# search_fields = ['name', 'user__email','Website', 'Phone']
# readonly_fields = ('user','Business','LastToken')
#     list_filter = ('Status',)
#     actions = ['accept_business', 'reject_business']
#
#     def confirmation_url(self, obj):
#         try:
#             confirmation = obj.user.BusinessConfirmations.all().order_by('id')[0]
#             return '<a href="%s%s">%s</a>' % ('/admin/ShoutWebsite/businessconfirmation/', confirmation.pk, obj.user)
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
class FeaturedTagAdmin(admin.ModelAdmin):
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
    list_display = ('id', 'type', 'usernames', 'object_id')
    filter_horizontal = ('users',)
    readonly_fields = ('last_message',)

    def usernames(self, conversation):
        return ', '.join([user.username for user in conversation.users.all()])
    usernames.short_description = 'Users'

admin.site.register(ConversationDelete)


admin.site.register(Message)
admin.site.register(MessageRead)
admin.site.register(MessageDelete)


# Message Attachment
class MessageAttachmentAdmin(admin.ModelAdmin):
    list_display = ('id', 'message', 'conversation', 'type', 'content_type', 'object_id', 'created_at')
    search_fields = ['message__id', 'conversation__id']

admin.site.register(MessageAttachment, MessageAttachmentAdmin)


# Report
@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ('type_name', 'user', 'text', 'attached_object', 'content_type', 'object_id', 'is_solved', 'is_disabled')
    list_filter = ('is_solved', 'is_disabled')
    actions = ['mark_as_solved', 'mark_as_disabled']
    readonly_fields = ('user', 'attached_object', 'content_type')

    def mark_as_solved(self, request, queryset):
        queryset.update(is_solved=True)

    mark_as_solved.short_description = "Mark selected reports as solved"

    def mark_as_disabled(self, request, queryset):
        queryset.update(is_disabled=True)

    mark_as_disabled.short_description = "Mark selected reports as disabled"


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
