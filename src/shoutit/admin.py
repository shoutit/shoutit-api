from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import UserChangeForm
from django import forms

from shoutit.models import User, Shout, Profile, ShoutWrap, StoredImage, Trade, Item, Experience, Stream, \
    FollowShip, Tag, Conversation, Message, Notification, Category, Currency, Business, BusinessConfirmation, BusinessCategory, \
    StoredFile, Report, PredefinedCity, LinkedFacebookAccount, LinkedGoogleAccount, MessageAttachment, Post, SharedLocation, Video, Stream2, \
    Listen, UserPermission, Permission, Conversation2, Message2, Message2Delete, Message2Read, Conversation2Delete, FeaturedTag

from django.utils.translation import ugettext_lazy as _


# Shout
class ShoutAdmin(admin.ModelAdmin):
    list_display = ('pk', 'date_published', 'user', 'text', 'country', 'city')
    readonly_fields = ('user', 'Streams', 'tags')

admin.site.register(Shout, ShoutAdmin)


# Trade
class TradeAdmin(admin.ModelAdmin):
    list_display = (
        'pk', 'base_date_published', 'Owner', 'OwnerProfile', 'type', 'item', 'text', 'country', 'city', 'is_sss', 'is_disabled')
    list_filter = ('type', 'is_sss', 'is_disabled')
    readonly_fields = ('user', 'Streams', 'tags', 'related_stream', 'recommended_stream', 'StreamsCode', 'item')

    def Owner(self, obj):
        return '<a href="%s%s" target="_blank">%s</a> | <a href="/user/%s" target="_blank">link</a>' % (
            '/admin/auth/user/', obj.user.username, obj.user, obj.user.username)

    Owner.allow_tags = True
    Owner.short_description = 'Owner User'

    def OwnerProfile(self, obj):
        if hasattr(obj.user, 'profile') and obj.user.profile:
            return '<a href="%s%s">%s</a>' % ('/admin/ShoutWebsite/userprofile/', obj.user.profile.pk, obj.user.profile)
        elif hasattr(obj.user, 'Business') and obj.user.Business:
            return '<a href="%s%s">%s</a>' % ('/admin/ShoutWebsite/businessprofile/', obj.user.Business.pk, obj.user.Business)

    OwnerProfile.allow_tags = True
    OwnerProfile.short_description = 'Owner Profile/Business'

admin.site.register(Trade, TradeAdmin)


# Post
class PostAdmin(admin.ModelAdmin):
    list_display = ('pk',  'user', 'type', 'text', 'country', 'city', 'muted', 'is_disabled')

admin.site.register(Post, PostAdmin)
admin.site.register(Item)


# Experience
class ExperienceAdmin(admin.ModelAdmin):
    list_display = ('pk', 'user', 'AboutBusiness', 'State', 'text')
    search_fields = ['AboutBusiness__name', 'text']
    readonly_fields = ('Streams', 'AboutBusiness')

admin.site.register(Experience, ExperienceAdmin)


class CustomUserChangeForm(UserChangeForm):
    username = forms.RegexField(
        label=_("Username"), max_length=30, min_length=2, regex=r"^[0-9a-zA-Z.]{2,30}$",
        help_text=_('Required. 2 to 30 characters and can only contain A-Z, a-z, 0-9, and periods (.)'),
        error_messages={
            'invalid': _("This value may only contain A-Z, a-z, 0-9, and periods (.)")})


class CustomUserAdmin(UserAdmin):
    save_on_top = True
    list_display = ('pk', 'username', 'email', 'first_name', 'last_name', 'is_staff', 'last_login')
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
    list_display = ('pk', 'name', 'user', 'country', 'city', 'Sex', 'image', 'Stream')
    search_fields = ['user__first_name', 'user__last_name', 'user__username', 'user__email', 'Bio', 'Mobile']
    readonly_fields = ('user', 'Stream', 'LastToken')
    list_filter = ('country', 'city', 'Sex')

admin.site.register(Profile, ProfileAdmin)


class LinkedFacebookAccountAdmin(admin.ModelAdmin):
    list_display = ('user', 'facebook_id', 'AccessToken', 'ExpiresIn')
    search_fields = ['user__first_name', 'user__last_name', 'user__username', 'user__email', 'facebook_id']

admin.site.register(LinkedFacebookAccount, LinkedFacebookAccountAdmin)


class LinkedGoogleAccountAdmin(admin.ModelAdmin):
    list_display = ('user', 'gplus_id')
    search_fields = ['user__first_name', 'user__last_name', 'user__username', 'user__email', 'facebook_id']

admin.site.register(LinkedGoogleAccount, LinkedGoogleAccountAdmin)


# Business
class BusinessProfileAdmin(admin.ModelAdmin):
    list_display = ('pk', 'name', 'user', 'country', 'city', 'Category', 'Confirmed', 'Stream')
    search_fields = ['name', 'user__email', 'Website', 'Mobile']
    readonly_fields = ('user', 'Stream', 'LastToken')

admin.site.register(Business, BusinessProfileAdmin)


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
#             confirmation = obj.user.BusinessConfirmations.all().order_by('pk')[0]
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
class BusinessConfirmationAdmin(admin.ModelAdmin):
    list_display = ('pk', 'user')

admin.site.register(BusinessConfirmation, BusinessConfirmationAdmin)


# BusinessCategory
class BusinessCategoryAdmin(admin.ModelAdmin):
    list_display = ('pk', 'name', 'Source', 'SourceID', 'Parent')
    search_fields = ['name', 'Parent__name']

admin.site.register(BusinessCategory, BusinessCategoryAdmin)


# FollowShip
class FollowShipAdmin(admin.ModelAdmin):
    list_display = ('pk', 'follower', 'stream', 'date_followed', 'state')
    search_fields = ['follower__user__username', 'stream__id']
    readonly_fields = ('follower', 'stream',)

admin.site.register(FollowShip, FollowShipAdmin)


# Tag
@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'Stream', 'stream2')
    search_fields = ('name',)


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


# Conversation
class ConversationAdmin(admin.ModelAdmin):
    list_display = ('pk', 'FromUser', 'ToUser', 'AboutPost')
    search_fields = ['FromUser__username', 'ToUser__username']


admin.site.register(Conversation, ConversationAdmin)
admin.site.register(Conversation2)
admin.site.register(Conversation2Delete)


# Message
class MessageAdmin(admin.ModelAdmin):
    list_display = ('pk', 'Conversation', 'FromUser', 'ToUser', 'text', 'DateCreated', 'is_read')
    search_fields = ['FromUser__username', 'ToUser__username', 'text']


admin.site.register(Message, MessageAdmin)
admin.site.register(Message2)
admin.site.register(Message2Read)
admin.site.register(Message2Delete)


# Message Attachment
class MessageAttachmentAdmin(admin.ModelAdmin):
    list_display = ('pk', 'message', 'conversation', 'type', 'content_type', 'object_id', 'created_at')
    search_fields = ['message__id', 'conversation__id']

admin.site.register(MessageAttachment, MessageAttachmentAdmin)


# Report
class ReportAdmin(admin.ModelAdmin):
    list_display = ('user', 'attached_object', 'content_type', 'text', 'IsSolved', 'is_disabled')
    list_filter = ('IsSolved', 'is_disabled')
    actions = ['mark_as_solved', 'mark_as_disabled']
    readonly_fields = ('user', 'attached_object', 'content_type')

    def mark_as_solved(self, request, queryset):
        queryset.update(IsSolved=True)

    mark_as_solved.short_description = "Mark selected reports as solved"

    def mark_as_disabled(self, request, queryset):
        queryset.update(is_disabled=True)

    mark_as_disabled.short_description = "Mark selected reports as disabled"


admin.site.register(Report)
admin.site.register(StoredFile)
admin.site.register(ShoutWrap)
admin.site.register(StoredImage)
admin.site.register(Video)
admin.site.register(Stream)
admin.site.register(Stream2)
admin.site.register(Listen)
admin.site.register(Notification)
admin.site.register(Category)
admin.site.register(Currency)
admin.site.register(PredefinedCity)
admin.site.register(SharedLocation)
admin.site.register(UserPermission)
admin.site.register(Permission)
