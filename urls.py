from django.conf.urls import patterns, include, url, handler500
from django.views.generic import TemplateView, RedirectView

from django.contrib import admin
admin.autodiscover()


# import apps.shoutit.controllers.payment_controller
# handler500 = 'apps.shoutit.tiered_views.general_views.handler500'

# TODO: general reg ex for all user names, tag names, etc
uuid_re = '[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}'

urlpatterns = patterns('',
                       # ## Admin ## #
                       url(r'^grappelli/', include('grappelli.urls')),  # grappelli URLS
                       url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
                       url(r'^admin/', include(admin.site.urls)),

                       # ##  Shout Website ## #
                       url(r'^$', 'apps.shoutit.tiered_views.general_views.index'),
                       url(r'^(requests|offers|experiences)/$', 'apps.shoutit.tiered_views.general_views.index',),
                       url(r'^(requests|offers|experiences)/([-\w]+)/(?:([a-z]+)/)?$', 'apps.shoutit.tiered_views.stream_views.browse'),

                       url(r'^tos/$', 'apps.shoutit.tiered_views.general_views.tos'),
                       url(r'^tos/$', 'apps.shoutit.tiered_views.general_views.tos'),
                       url(r'^privacy/$', 'apps.shoutit.tiered_views.general_views.privacy'),
                       url(r'^rules/$', 'apps.shoutit.tiered_views.general_views.rules'),
                       url(r'^learnmore/$', 'apps.shoutit.tiered_views.general_views.learnmore'),
                       url(r'^xhr/shouts/stream/$', 'apps.shoutit.tiered_views.stream_views.index_stream'),
                       url(r'^xhr/shouts/livetimeline/(?:([-\w]+)/)?$', 'apps.shoutit.tiered_views.stream_views.livetimeline'),
                       url(r'^xhr/live_events/$', 'apps.shoutit.tiered_views.general_views.live_events'),
                       url(r'^xhr/delete_event/([-\w]+)/$', 'apps.shoutit.tiered_views.general_views.delete_event'),

                       url(r'^(?:xhr/)?signup/$', 'apps.shoutit.tiered_views.user_views.signup'),
                       url(r'^(?:xhr/)?signin/$', 'apps.shoutit.tiered_views.user_views.signin'),
                       url(r'^(?:xhr/)?signout/$', 'apps.shoutit.tiered_views.user_views.signout'),
                       url(r'^(?:xhr/)?recover/$', 'apps.shoutit.tiered_views.user_views.recover'),
                       url(r'^(?:xhr/)?recover_business_activation/$', 'apps.shoutit.tiered_views.business_views.recover_activation'),


                       # url(r'^^(?:xhr/)?bsignup/', 'apps.shoutit.tiered_views.business_views.signup'),
                       url(r'^^(?:xhr/)?bsignup/(?:([-\w]+)/)?$', 'apps.shoutit.tiered_views.business_views.signup'),
                       url(r'^^(?:xhr/)?subscribe/$', 'apps.shoutit.tiered_views.business_views.subscribe'),
                       url(r'^^(?:xhr/)?btempsignup/(?:([-\w]+)/)?$', 'apps.shoutit.tiered_views.business_views.signup_temp'),

                       url(r'^(?:xhr/)?shout/buy/$', 'apps.shoutit.tiered_views.shout_views.shout_buy'),
                       url(r'^(?:xhr/)?shout/sell/$', 'apps.shoutit.tiered_views.shout_views.shout_sell'),
                       url(r'^(?:shout|request|offer)/([-\w]+)/', 'apps.shoutit.tiered_views.shout_views.shout_view'),
                       url(r'^(?:xhr/)?shout/([-\w]+)/edit/$', 'apps.shoutit.tiered_views.shout_views.shout_edit'),
                       url(r'^(?:xhr/)?shout/([-\w]+)/renew/$', 'apps.shoutit.tiered_views.shout_views.renew_shout'),

                       url(r'^user/(\w+)/$', 'apps.shoutit.tiered_views.user_views.user_profile'),
                       url(r'^xhr/user/(\w+)/stream/?$', 'apps.shoutit.tiered_views.user_views.user_stream'),
                       url(r'^xhr/user/(\w+)/activities_stream/?$', 'apps.shoutit.tiered_views.user_views.activities_stream'),
                       url(r'^(?:xhr/)?user/(\w+)/editProfile/$', 'apps.shoutit.tiered_views.user_views.user_edit_profile'),

                       url(r'^(?:xhr/)?user/(\w+)/editBusinessProfile/$', 'apps.shoutit.tiered_views.business_views.business_edit_profile'),

                       url(r'^tag/([^/]+)/$', 'apps.shoutit.tiered_views.tag_views.tag_profile'),
                       url(r'^xhr/tag/([^/]+)/stream/?$', 'apps.shoutit.tiered_views.tag_views.tag_stream'),

                       url(r'^(?:xhr/)?reply/([-\w]+)/(?:([-\w]+)/)?$', 'apps.shoutit.tiered_views.message_views.send_message'),


                       url(r'^xhr/delete_conversation/([-\w]+)/$', 'apps.shoutit.tiered_views.message_views.delete_conversation'),
                       url(r'^xhr/delete_message/([-\w]+)/([-\w]+)/$', 'apps.shoutit.tiered_views.message_views.delete_message'),
                       url(r'^xhr/getHtmlMessage/$', 'apps.shoutit.tiered_views.message_views.get_html_message'),

                       url(r'^messages/$', 'apps.shoutit.tiered_views.message_views.read_conversations'),
                       url(r'^(?:xhr/)?messages/stream/$', 'apps.shoutit.tiered_views.message_views.read_conversations_stream'),

                       url(r'^(?:xhr/)?messages/([-\w]+)/$', 'apps.shoutit.tiered_views.message_views.read_conversation'),
                       url(r'^xhr/message/([-\w]+)/read/$', 'apps.shoutit.tiered_views.message_views.mark_message_as_read'),

                       url(r'^upload/files/$', 'apps.shoutit.tiered_views.general_views.upload_file'),
                       url(r'^upload/([\w_-]+)/$', 'apps.shoutit.tiered_views.shout_views.upload_image'),

                       url(r'notifications/$', 'apps.shoutit.tiered_views.realtime_views.notifications'),
                       url(r'^xhr/notifications/count/$', 'apps.shoutit.tiered_views.realtime_views.notifications_count'),

                       #	url(r'pub_realtime/$', 'apps.shoutit.views.redirect_to_node'),

                       # ## API ## #

                       url(r'^api/', include('apps.shoutit.api.urls')),

                       url(r'^oauth/request_token/$', 'apps.shoutit.api.authentication.get_request_token'),
                       url(r'^oauth/access_token/(\w+)/$', 'apps.shoutit.api.authentication.get_access_token_using_social_channel'),
                       # url(r'^oauth/access_token/$', 'apps.shoutit.api.authentication.get_basic_access_token'),

                       # ## XHR ## #
                       url(r'^xhr/user/$', 'apps.shoutit.tiered_views.user_views.search_user'),
                       url(r'^xhr/user/(\w+)/start_listening/$', 'apps.shoutit.tiered_views.user_views.start_listening_to_user'),
                       url(r'^xhr/user/(\w+)/stop_listening/$', 'apps.shoutit.tiered_views.user_views.stop_listening_to_user'),
                       url(r'^xhr/user/(\w+)/(listeners|listening)/(?:(\w+)/)?(?:(\w+)/)?$',
                           'apps.shoutit.tiered_views.user_views.user_stats'),

                       url(r'^xhr/tag/$', 'apps.shoutit.tiered_views.tag_views.search_tag'),
                       url(r'^xhr/tag/([^/]+)/start_listening/$', 'apps.shoutit.tiered_views.tag_views.start_listening_to_tag'),
                       url(r'^xhr/tag/([^/]+)/stop_listening/$', 'apps.shoutit.tiered_views.tag_views.stop_listening_to_tag'),
                       url(r'^xhr/tag/([^/]+)/listeners/$', 'apps.shoutit.tiered_views.tag_views.tag_stats'),

                       url(r'^xhr/(user|tag)/([\.\w-]+)/picture(?:/(\d+))?/$', 'apps.shoutit.tiered_views.general_views.profile_picture'),

                       url(r'^(?:xhr/)?image/([-\w]+)(?:/(\d+))?/(?:i\.png)?$',
                           'apps.shoutit.tiered_views.general_views.stored_image'),

                       url(r'^xhr/top_tags/$', 'apps.shoutit.tiered_views.tag_views.top_tags'),


                       url(r'^xhr/hovercard/$', 'apps.shoutit.tiered_views.general_views.hovercard'),
                       url(r'^xhr/shout/nearby/$', 'apps.shoutit.tiered_views.shout_views.nearby_shouts'),
                       url(r'^xhr/loadShout/([a-zA-z0-9]+)/$', 'apps.shoutit.tiered_views.shout_views.load_shout'),
                       url(r'^xhr/deleteShout/$', 'apps.shoutit.tiered_views.shout_views.delete_shout'),
                       url(r'^xhr/update_location/$', 'apps.shoutit.tiered_views.user_views.update_user_location'),
                       url(r'^xhr/setTagParent/$', 'apps.shoutit.tiered_views.tag_views.set_tag_parent'),

                       url(r'^sts/$', 'apps.shoutit.tiered_views.general_views.admin_stats'),

                       url(r'^reactivate/$', 'apps.shoutit.tiered_views.user_views.resend_activation'),
                       url(r'^xhr/reactivate/$', 'apps.shoutit.tiered_views.user_views.resend_activation'),
                       url(r'^favicon\.ico$', RedirectView.as_view(url='static/img/icon.png')),
                       url(r'^robots\.txt/$', TemplateView.as_view(template_name='robots.txt', content_type='text/plain')),
                       url(r'^googlebc700f17ba42dd9f\.html/$',
                           TemplateView.as_view(template_name='googlebc700f17ba42dd9f.html', content_type='text/plain')),

                       url(r'^activate/$', 'apps.shoutit.tiered_views.user_views.activate_user'),
                       url(r'^xhr/activate/$', 'apps.shoutit.tiered_views.user_views.activate_user'),

                       url(r'^confirm_business/', 'apps.shoutit.tiered_views.business_views.confirm_business'),
                       url(r'^xhr/confirm_business/', 'apps.shoutit.tiered_views.business_views.confirm_business'),

                       url(r'^create_tiny_business/', 'apps.shoutit.tiered_views.business_views.create_tiny_business'),
                       url(r'^xhr/create_tiny_business/', 'apps.shoutit.tiered_views.business_views.create_tiny_business'),

                       url(r'^modal/(?:(\w+)/)?$', 'apps.shoutit.tiered_views.general_views.modal'),

                       url(r'^(?:xhr/)?shout_deal/', 'apps.shoutit.tiered_views.deal_views.shout_deal'),
                       url(r'^(?:xhr/)?close_deal/([a-zA-z0-9]+)/', 'apps.shoutit.tiered_views.deal_views.close_deal'),
                       url(r'^(?:xhr/)?valid_voucher/', 'apps.shoutit.tiered_views.deal_views.is_voucher_valid'),
                       url(r'^(?:xhr/)?invalidate_voucher/', 'apps.shoutit.tiered_views.deal_views.invalidate_voucher'),
                       url(r'^(?:xhr/)?deal/([a-zA-z0-9]+)/$', 'apps.shoutit.tiered_views.deal_views.view_deal'),
                       url(r'^(?:xhr/)?deals/$', 'apps.shoutit.tiered_views.deal_views.view_deals'),
                       url(r'^xhr/deals_stream/(\w+)/(?:(\d+)/)?$', 'apps.shoutit.tiered_views.deal_views.deals_stream'),

                       url(r'^set_perma/$', 'apps.shoutit.tiered_views.general_views.set_perma'),

                       # Facebook Stuff
                       url(r'^fb_auth/$', 'apps.shoutit.tiered_views.user_views.fb_auth'),
                       url(r'^fb/connect/$', 'apps.shoutit.tiered_views.fb_views.fb_connect'),
                       url(r'^fb/share/$', 'apps.shoutit.tiered_views.fb_views.fb_share'),
                       url(r'^fb/tab/$', 'apps.shoutit.tiered_views.fb_views.fb_tab'),
                       url(r'^fb/tab_edit/$', 'apps.shoutit.tiered_views.fb_views.fb_tab_edit'),
                       url(r'^fb/comp/(\d+)/$', 'apps.shoutit.tiered_views.fb_views.fb_comp'),
                       url(r'^fb/comp_page/(\d+)/$', 'apps.shoutit.tiered_views.fb_views.fb_comp_page'),
                       url(r'^fb/comp_add/(\d+)/(\w+)/(\w+)/(\w+)/$', 'apps.shoutit.tiered_views.fb_views.fb_comp_add'),

                       # Google Stuff
                       url(r'^gplus_auth/$', 'apps.shoutit.tiered_views.user_views.gplus_auth'),

                       url(r'^set_language/', 'apps.shoutit.tiered_views.general_views.set_language'),
                       url(r'^jsi18n/$', 'django.views.i18n.javascript_catalog', {'packages': ('apps.shoutit',)}),

                       url(r'^(?:bad-|good-)?experience/([-\w]+)/', 'apps.shoutit.tiered_views.experience_views.view_experience'),
                       url(r'^xhr/experiences_stream/(\w+)/(?:(\d+)/)?$', 'apps.shoutit.tiered_views.experience_views.experiences_stream'),
                       url(r'^xhr/post_experience/(?:(\w+)/)?$', 'apps.shoutit.tiered_views.experience_views.post_exp'),
                       url(r'^xhr/share_experience/([-\w]+)/$', 'apps.shoutit.tiered_views.experience_views.share_experience'),
                       url(r'^xhr/edit_experience/([-\w]+)/$', 'apps.shoutit.tiered_views.experience_views.edit_experience'),
                       url(r'^xhr/users_shared_experience/([-\w]+)/$',
                           'apps.shoutit.tiered_views.experience_views.users_shared_experience'),

                       url(r'^xhr/comment_on_post/([-\w]+)/$', 'apps.shoutit.tiered_views.comment_views.comment_on_post'),
                       url(r'^xhr/post_comments/([-\w]+)/$', 'apps.shoutit.tiered_views.comment_views.post_comments'),
                       url(r'^xhr/delete_comment/([-\w]+)/$', 'apps.shoutit.tiered_views.comment_views.delete_comment'),

                       url(r'^xhr/gallery_items_stream/(\w+)/(?:(\d+)/)?$', 'apps.shoutit.tiered_views.gallery_views.galleryItems_stream'),
                       url(r'^xhr/add_gallery_item/([-\w]+)/$', 'apps.shoutit.tiered_views.gallery_views.add_gallery_item'),
                       url(r'^xhr/delete_gallery_item/([-\w]+)/$', 'apps.shoutit.tiered_views.gallery_views.delete_gallery_item'),
                       url(r'^xhr/shout_item/([-\w]+)/$', 'apps.shoutit.tiered_views.gallery_views.shout_item'),
                       url(r'^xhr/edit_item/([-\w]+)/$', 'apps.shoutit.tiered_views.gallery_views.edit_item'),

                       url(r'^xhr/report/(\d+)/([-\w]+)/$', 'apps.shoutit.tiered_views.report_views.report'),
                       url(r'^xhr/delete_comment/([-\w]+)/$', 'apps.shoutit.tiered_views.comment_views.delete_comment'),
                       url(r'^paypal/$', 'apps.shoutit.tiered_views.deal_views.paypal'),
                       url(r'^paypal_return/$', 'apps.shoutit.tiered_views.payment_views.pdt'),
                       url(r'^cpsp_(\w+)/$', 'apps.shoutit.tiered_views.deal_views.cpsp_action'),


                       url(r'^contact-import/$', 'apps.shoutit.tiered_views.user_views.import_contacts', name='import_contacts'),
                       url(r'^(?:xhr/)?send_invitations/$', 'apps.shoutit.tiered_views.user_views.send_invitations'),

                       # user
                       url(r'^([\w.]+)$', 'apps.shoutit.tiered_views.user_views.user_profile'),

                       # url(r'^([abcdefghklmnopqrstuvwxyzABCDEFGHKLMNPQRSTUVWXYZ23456789]+)/$',
                       #     'apps.shoutit.tiered_views.user_views.activate_modal'),

)

#urlpatterns += patterns('',
#	url(r'^admin/django-lean/', include('django_lean.experiments.admin_urls')),
#	url(r'^django-lean/', include('django_lean.experiments.urls')),
#)