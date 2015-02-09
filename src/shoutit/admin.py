from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import UserChangeForm
from django import forms

from shoutit.models import User, Shout, Profile, ConfirmToken, ShoutWrap, StoredImage, Trade, Item, Experience, Stream, \
    FollowShip, Tag, Conversation, Message, Notification, Category, Currency, Business, BusinessConfirmation, BusinessCategory, \
    StoredFile, Report, PredefinedCity, LinkedFacebookAccount, LinkedGoogleAccount, MessageAttachment

# from activity_logger.models import Activity, ActivityData, Request
# from shoutit.controllers import business_controller
from django.utils.translation import ugettext_lazy as _


# Shout
class ShoutAdmin(admin.ModelAdmin):
    list_display = ('pk', 'DatePublished', 'OwnerUser', 'Text', 'CountryCode', 'ProvinceCode')
    readonly_fields = ('OwnerUser', 'Streams', 'Tags')


admin.site.register(Shout, ShoutAdmin)


# Trade
class TradeAdmin(admin.ModelAdmin):
    list_display = (
        'pk', 'BaseDatePublished', 'Owner', 'OwnerProfile', 'Type', 'Item', 'Text', 'CountryCode', 'ProvinceCode', 'IsSSS', 'IsDisabled')
    list_filter = ('Type', 'IsSSS', 'IsDisabled')
    readonly_fields = ('OwnerUser', 'Streams', 'Tags', 'RelatedStream', 'RecommendedStream', 'StreamsCode', 'Item')

    def Owner(self, obj):
        return '<a href="%s%s" target="_blank">%s</a> | <a href="/user/%s" target="_blank">link</a>' % (
            '/admin/auth/user/', obj.OwnerUser.username, obj.OwnerUser, obj.OwnerUser.username)

    Owner.allow_tags = True
    Owner.short_description = 'Owner User'

    def OwnerProfile(self, obj):
        if hasattr(obj.OwnerUser, 'profile') and obj.OwnerUser.profile:
            return '<a href="%s%s">%s</a>' % ('/admin/ShoutWebsite/userprofile/', obj.OwnerUser.profile.pk, obj.OwnerUser.profile)
        elif hasattr(obj.OwnerUser, 'Business') and obj.OwnerUser.Business:
            return '<a href="%s%s">%s</a>' % ('/admin/ShoutWebsite/businessprofile/', obj.OwnerUser.Business.pk, obj.OwnerUser.Business)

    OwnerProfile.allow_tags = True
    OwnerProfile.short_description = 'Owner Profile/Business'


admin.site.register(Trade, TradeAdmin)

admin.site.register(Item)


# Experience
class ExperienceAdmin(admin.ModelAdmin):
    list_display = ('pk', 'OwnerUser', 'AboutBusiness', 'State', 'Text')
    search_fields = ['AboutBusiness__Name', 'Text']
    readonly_fields = ('Streams', 'AboutBusiness')


admin.site.register(Experience, ExperienceAdmin)


class CustomUserChangeForm(UserChangeForm):
    username = forms.RegexField(
        label=_("Username"), min_length=2, max_length=30, regex=r"^[\w.]+$",
        help_text=_("Required. 2 to 30 characters. Letters, digits and ./_ only."),
        error_messages={
            'invalid': _("This value may contain only letters, numbers and ./_ characters.")})


class CustomUserAdmin(UserAdmin):
    save_on_top = True
    list_display = ('pk', 'username', 'email', 'first_name', 'last_name', 'is_staff', 'last_login')
    # list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'last_login', 'request_count')
    list_per_page = 50

    form = CustomUserChangeForm


admin.site.register(User, CustomUserAdmin)


# Profile
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('pk', 'name', 'user', 'Country', 'City', 'Sex', 'image', 'Stream')
    search_fields = ['user__first_name', 'user__last_name', 'user__username', 'user__email', 'Bio', 'Mobile']
    readonly_fields = ('user', 'Stream', 'LastToken')
    list_filter = ('Country', 'City', 'Sex')


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
    list_display = ('pk', 'name', 'user', 'Country', 'City', 'Category', 'Confirmed', 'Stream')
    search_fields = ['Name', 'user__email', 'Website', 'Mobile']
    readonly_fields = ('user', 'Stream', 'LastToken')


admin.site.register(Business, BusinessProfileAdmin)


# BusinessCreateApplication
# class BusinessCreateApplicationAdmin(admin.ModelAdmin):
# list_display = ('Name', 'user', 'Business','confirmation_url','Country', 'City', 'Status')
# search_fields = ['Name', 'user__email','Website', 'Phone']
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
    list_display = ('pk', 'Name', 'Source', 'SourceID', 'Parent')
    search_fields = ['Name', 'Parent__Name']


admin.site.register(BusinessCategory, BusinessCategoryAdmin)


# FollowShip
class FollowShipAdmin(admin.ModelAdmin):
    list_display = ('pk', 'follower', 'stream', 'date_followed', 'state')
    search_fields = ['follower__user__username', 'stream__pk']
    readonly_fields = ('follower', 'stream',)


admin.site.register(FollowShip, FollowShipAdmin)


# Tag
class TagAdmin(admin.ModelAdmin):
    list_display = ('pk', 'Name', 'Stream')
    search_fields = ['pk', 'Name']


admin.site.register(Tag, TagAdmin)


# Conversation
class ConversationAdmin(admin.ModelAdmin):
    list_display = ('pk', 'FromUser', 'ToUser', 'AboutPost')
    search_fields = ['FromUser__username', 'ToUser__username']


admin.site.register(Conversation, ConversationAdmin)


# Message
class MessageAdmin(admin.ModelAdmin):
    list_display = ('pk', 'Conversation', 'FromUser', 'ToUser', 'Text', 'DateCreated', 'IsRead')
    search_fields = ['FromUser__username', 'ToUser__username', 'Text']


admin.site.register(Message, MessageAdmin)


# Message Attachment
class MessageAttachmentAdmin(admin.ModelAdmin):
    list_display = ('pk', 'message', 'conversation', 'content_type', 'object_id', 'created_at')
    search_fields = ['message__id', 'conversation__id']


admin.site.register(MessageAttachment, MessageAttachmentAdmin)


# Request
class RequestAdmin(admin.ModelAdmin):
    list_display = ('ip_address', 'plain_url', 'user', 'method', 'date_visited', 'referer')
    search_fields = ['ip_address', 'plain_url', 'user__username', 'referer']


# admin.site.register(Request, RequestAdmin)


# Report
class ReportAdmin(admin.ModelAdmin):
    list_display = ('user', 'attached_object', 'content_type', 'Text', 'IsSolved', 'IsDisabled')
    list_filter = ('IsSolved', 'IsDisabled')
    actions = ['mark_as_solved', 'mark_as_disabled']
    readonly_fields = ('user', 'attached_object', 'content_type')

    def mark_as_solved(self, request, queryset):
        queryset.update(IsSolved=True)

    mark_as_solved.short_description = "Mark selected reports as solved"

    def mark_as_disabled(self, request, queryset):
        queryset.update(IsDisabled=True)

    mark_as_disabled.short_description = "Mark selected reports as disabled"


admin.site.register(Report)

admin.site.register(StoredFile)
admin.site.register(ConfirmToken)
admin.site.register(ShoutWrap)
admin.site.register(StoredImage)
admin.site.register(Stream)
admin.site.register(Notification)
admin.site.register(Category)
admin.site.register(Currency)
admin.site.register(PredefinedCity)
# admin.site.register(Activity)
# admin.site.register(ActivityData)
