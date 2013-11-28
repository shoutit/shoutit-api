from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin
from apps.ActivityLogger.models import Activity, ActivityData, Request
from apps.shoutit.controllers import business_controller
from apps.shoutit.models.models import Shout, UserProfile, ConfirmToken, ShoutWrap, StoredImage, Trade, Item, Experience, Stream, FollowShip, Store, Tag, Badge, Conversation, Message, Notification, Category, Currency, BusinessProfile, BusinessConfirmation, BusinessCategory, StoredFile, Report, BusinessCreateApplication

# Shout
class ShoutAdmin(admin.ModelAdmin):
	list_display = ('id','DatePublished','OwnerUser', 'Text','CountryCode','ProvinceCode' )
	readonly_fields = ('OwnerUser','Streams','Tags')

admin.site.register(Shout,ShoutAdmin)

# Trade
class TradeAdmin(admin.ModelAdmin):
	list_display = ('id','BaseDatePublished','Owner','OwnerProfile', 'Type','Item','Text','CountryCode','ProvinceCode' ,'IsSSS' ,'IsDisabled')
	list_filter = ('Type', 'IsSSS', 'IsDisabled')
	readonly_fields = ('OwnerUser','Streams','Tags','RelatedStream','RecommendedStream','StreamsCode','Item')
	def Owner(self, obj):
		return '<a href="%s%s" target="_blank">%s</a> | <a href="/user/%s" target="_blank">link</a>' % ('/admin/auth/user/', obj.OwnerUser.username, obj.OwnerUser, obj.OwnerUser.username)
	Owner.allow_tags = True
	Owner.short_description = 'Owner User'

	def OwnerProfile(self, obj):
		if hasattr(obj.OwnerUser,'Profile') and obj.OwnerUser.Profile:
			return '<a href="%s%s">%s</a>' % ('/admin/ShoutWebsite/userprofile/', obj.OwnerUser.Profile.id, obj.OwnerUser.Profile)
		elif hasattr(obj.OwnerUser, 'Business') and obj.OwnerUser.Business:
			return '<a href="%s%s">%s</a>' % ('/admin/ShoutWebsite/businessprofile/', obj.OwnerUser.Business.id, obj.OwnerUser.Business)
	OwnerProfile.allow_tags = True
	OwnerProfile.short_description = 'Owner Profile/Business'

admin.site.register(Trade, TradeAdmin)

admin.site.register(Item)

# Experience
class ExperienceAdmin(admin.ModelAdmin):
	list_display = ('pk', 'OwnerUser','AboutBusiness', 'State','Text')
	search_fields = ['AboutBusiness__Name','Text']
	readonly_fields = ('Streams','AboutBusiness')
admin.site.register(Experience, ExperienceAdmin)

# User
admin.site.unregister(User)
class CustomUserAdmin(UserAdmin):
	save_on_top = True
	list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'last_login','request_count')
	list_per_page = 50
admin.site.register(User, CustomUserAdmin)

# UserProfile
class UserProfileAdmin(admin.ModelAdmin):
	list_display = ('name','User', 'Country','City' , 'Sex','Image','Stream')
	search_fields = ['User__first_name','User__last_name','User__username', 'User__email','Bio', 'Mobile']
	readonly_fields = ('User','Stream','LastToken','Interests')
	list_filter = ('Country', 'City', 'Sex')

admin.site.register(UserProfile, UserProfileAdmin)

# BusinessProfile
class BusinessProfileAdmin(admin.ModelAdmin):
	list_display = ('name', 'User', 'Country', 'City','Category', 'Confirmed', 'Stream')
	search_fields = ['Name', 'User__email','Website', 'Mobile']
	readonly_fields = ('User','Stream','LastToken')
admin.site.register(BusinessProfile, BusinessProfileAdmin)

# BusinessCreateApplication
class BusinessCreateApplicationAdmin(admin.ModelAdmin):
	list_display = ('Name', 'User', 'Business','confirmation_url','Country', 'City', 'Status')
	search_fields = ['Name', 'User__email','Website', 'Phone']
	readonly_fields = ('User','Business','LastToken')
	list_filter = ('Status',)
	actions = ['accept_business', 'reject_business']

	def confirmation_url(self, obj):
		try:
			confirmation = obj.User.BusinessConfirmations.all().order_by('id')[0]
			return '<a href="%s%s">%s</a>' % ('/admin/ShoutWebsite/businessconfirmation/', confirmation.id, obj.User)
		except :
			return 'Docs not yet submitted'

	confirmation_url.allow_tags = True
	confirmation_url.short_description = 'Confirmation Link'

	def accept_business(self, request, queryset):
		for q in queryset:
			business_controller.AcceptBusiness(request, q)
	accept_business.short_description = "Accept selected business creation applications"

	def reject_business(self, request, queryset):
		pass
	#TODO send email with explanation to user via email
	reject_business.short_description = "Reject selected business creation applications"
admin.site.register(BusinessCreateApplication, BusinessCreateApplicationAdmin)

# BusinessConfirmation
class BusinessConfirmationAdmin(admin.ModelAdmin):
	list_display = ('id', 'User')
admin.site.register(BusinessConfirmation, BusinessConfirmationAdmin)

# BusinessCategory
class BusinessCategoryAdmin(admin.ModelAdmin):
	list_display = ('id', 'Name', 'Source', 'SourceID', 'Parent')
	search_fields = ['Name','Parent__Name']
admin.site.register(BusinessCategory, BusinessCategoryAdmin)

# FollowShip
class FollowShipAdmin(admin.ModelAdmin):
	list_display = ('pk', 'follower', 'stream','date_followed','state')
	search_fields = ['follower__User__username','stream__id']
	readonly_fields = ('follower','stream',)
admin.site.register(FollowShip,FollowShipAdmin)

# Tag
class TagAdmin(admin.ModelAdmin):
	list_display = ('id','Name','Stream')
	search_fields = ['id', 'Name']
admin.site.register(Tag, TagAdmin)

# Conversation
class ConversationAdmin(admin.ModelAdmin):
	list_display = ('FromUser','ToUser', 'AboutPost')
	search_fields = ['FromUser__username', 'ToUser__username']
admin.site.register(Conversation, ConversationAdmin)

# Message
class MessageAdmin(admin.ModelAdmin):
	list_display = ('Conversation', 'FromUser','ToUser', 'Text', 'DateCreated', 'IsRead')
	search_fields = ['FromUser__username', 'ToUser__username', 'Text']
admin.site.register(Message, MessageAdmin)

# Request
class RequestAdmin(admin.ModelAdmin):
	list_display = ('ip_address','plain_url','user','method','date_visited','referer')
	search_fields = ['ip_address','plain_url','user__username','referer']
admin.site.register(Request, RequestAdmin)

# Report
class ReportAdmin(admin.ModelAdmin):
	list_display = ('User', 'AttachedObject', 'content_type', 'Text', 'IsSolved', 'IsDisabled')
	list_filter = ('IsSolved', 'IsDisabled')
	actions = ['mark_as_solved','mark_as_disabled']
	readonly_fields = ('User','AttachedObject','content_type')


	def mark_as_solved(self, request, queryset):
		queryset.update(IsSolved = True)
	mark_as_solved.short_description = "Mark selected reports as solved"

	def mark_as_disabled(self, request, queryset):
		queryset.update(IsDisabled = True)
	mark_as_disabled.short_description = "Mark selected reports as disabled"
admin.site.register(Report)

admin.site.register(StoredFile)
admin.site.register(ConfirmToken)
admin.site.register(ShoutWrap)
admin.site.register(StoredImage)
admin.site.register(Stream)
admin.site.register(Store)
admin.site.register(Badge)
admin.site.register(Notification)
admin.site.register(Category)
admin.site.register(Currency)
admin.site.register(Activity)
admin.site.register(ActivityData)

