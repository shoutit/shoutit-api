from django.conf.urls import patterns, include, url, handler500
from django.views.generic import TemplateView, RedirectView

from django.contrib import admin

admin.autodiscover()


# import shoutit.controllers.payment_controller
# handler500 = 'shoutit.tiered_views.general_views.handler500'

# TODO: general reg ex for all user names, tag names, etc
uuid_re = '[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}'

urlpatterns = patterns('',
                       # ## Admin ## #
                       url(r'^grappelli/', include('grappelli.urls')),  # grappelli URLS
                       url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
                       url(r'^admin/', include(admin.site.urls)),

                       # ##  Shout Website ## #
                       url(r'^$', 'shoutit.tiered_views.general_views.index'),
                       url(r'^(requests|offers|experiences)/$', 'shoutit.tiered_views.general_views.index', ),
                       url(r'^(requests|offers|experiences)/([-\w]+)/(?:([a-z]+)/)?$', 'shoutit.tiered_views.stream_views.browse'),

                       url(r'^tos/$', 'shoutit.tiered_views.general_views.tos'),
                       url(r'^tos/$', 'shoutit.tiered_views.general_views.tos'),
                       url(r'^privacy/$', 'shoutit.tiered_views.general_views.privacy'),
                       url(r'^rules/$', 'shoutit.tiered_views.general_views.rules'),
                       url(r'^learnmore/$', 'shoutit.tiered_views.general_views.learnmore'),
                       url(r'^xhr/shouts/stream/$', 'shoutit.tiered_views.stream_views.index_stream'),
                       url(r'^xhr/shouts/livetimeline/(?:([-\w]+)/)?$', 'shoutit.tiered_views.stream_views.livetimeline'),
                       url(r'^xhr/live_events/$', 'shoutit.tiered_views.general_views.live_events'),
                       url(r'^xhr/delete_event/([-\w]+)/$', 'shoutit.tiered_views.general_views.delete_event'),

                       url(r'^(?:xhr/)?signup/$', 'shoutit.tiered_views.user_views.signup'),
                       url(r'^(?:xhr/)?signin/$', 'shoutit.tiered_views.user_views.signin'),
                       url(r'^(?:xhr/)?signout/$', 'shoutit.tiered_views.user_views.signout'),
                       url(r'^(?:xhr/)?recover/$', 'shoutit.tiered_views.user_views.recover'),
                       url(r'^(?:xhr/)?recover_business_activation/$', 'shoutit.tiered_views.business_views.recover_activation'),


                       # url(r'^^(?:xhr/)?bsignup/', 'shoutit.tiered_views.business_views.signup'),
                       url(r'^^(?:xhr/)?bsignup/(?:([-\w]+)/)?$', 'shoutit.tiered_views.business_views.signup'),
                       url(r'^^(?:xhr/)?subscribe/$', 'shoutit.tiered_views.business_views.subscribe'),
                       url(r'^^(?:xhr/)?btempsignup/(?:([-\w]+)/)?$', 'shoutit.tiered_views.business_views.signup_temp'),

                       url(r'^(?:xhr/)?shout/buy/$', 'shoutit.tiered_views.shout_views.post_request'),
                       url(r'^(?:xhr/)?shout/sell/$', 'shoutit.tiered_views.shout_views.post_offer'),
                       url(r'^(?:shout|request|offer)/([-\w]+)/', 'shoutit.tiered_views.shout_views.shout_view'),
                       url(r'^(?:xhr/)?shout/([-\w]+)/edit/$', 'shoutit.tiered_views.shout_views.shout_edit'),
                       url(r'^(?:xhr/)?shout/([-\w]+)/renew/$', 'shoutit.tiered_views.shout_views.renew_shout'),
                       url(r'^(?:xhr/)?shout/([-\w]+)/delete/$', 'shoutit.tiered_views.shout_views.delete_shout'),

                       url(r'^user/(\w+)/$', 'shoutit.tiered_views.user_views.user_profile'),
                       url(r'^xhr/user/(\w+)/stream/?$', 'shoutit.tiered_views.user_views.user_stream'),
                       url(r'^xhr/user/(\w+)/activities_stream/?$', 'shoutit.tiered_views.user_views.activities_stream'),
                       url(r'^(?:xhr/)?user/(\w+)/editProfile/$', 'shoutit.tiered_views.user_views.user_edit_profile'),

                       url(r'^(?:xhr/)?user/(\w+)/editBusinessProfile/$', 'shoutit.tiered_views.business_views.business_edit_profile'),

                       url(r'^tag/([^/]+)/$', 'shoutit.tiered_views.tag_views.tag_profile'),
                       url(r'^xhr/tag/([^/]+)/stream/?$', 'shoutit.tiered_views.tag_views.tag_stream'),

                       url(r'^(?:xhr/)?reply/([-\w]+)/(?:([-\w]+)/)?$', 'shoutit.tiered_views.message_views.send_message'),


                       url(r'^xhr/delete_conversation/([-\w]+)/$', 'shoutit.tiered_views.message_views.delete_conversation'),
                       url(r'^xhr/delete_message/([-\w]+)/([-\w]+)/$', 'shoutit.tiered_views.message_views.delete_message'),
                       url(r'^xhr/getHtmlMessage/$', 'shoutit.tiered_views.message_views.get_html_message'),

                       url(r'^messages/$', 'shoutit.tiered_views.message_views.read_conversations'),
                       url(r'^(?:xhr/)?messages/stream/$', 'shoutit.tiered_views.message_views.read_conversations_stream'),

                       url(r'^(?:xhr/)?messages/([-\w]+)/$', 'shoutit.tiered_views.message_views.read_conversation'),
                       url(r'^xhr/message/([-\w]+)/read/$', 'shoutit.tiered_views.message_views.mark_message_as_read'),

                       url(r'^upload/files/$', 'shoutit.tiered_views.general_views.upload_file'),
                       url(r'^upload/([\w_-]+)/$', 'shoutit.tiered_views.shout_views.upload_image'),

                       url(r'^notifications/$', 'shoutit.tiered_views.realtime_views.notifications'),
                       url(r'^xhr/notifications/count/$', 'shoutit.tiered_views.realtime_views.notifications_count'),

                       # url(r'pub_realtime/$', 'shoutit.views.redirect_to_node'),

                       # ## API ## #

                       url(r'^api/', include('shoutit.api.urls')),

                       url(r'^oauth/request_token/$', 'shoutit.api.authentication.get_request_token'),
                       url(r'^oauth/access_token/(\w+)/$', 'shoutit.api.authentication.get_access_token_using_social_channel'),
                       # url(r'^oauth/access_token/$', 'shoutit.api.authentication.get_basic_access_token'),

                       # ## XHR ## #
                       url(r'^xhr/user/$', 'shoutit.tiered_views.user_views.search_user'),
                       url(r'^xhr/user/(\w+)/start_listening/$', 'shoutit.tiered_views.user_views.start_listening_to_user'),
                       url(r'^xhr/user/(\w+)/stop_listening/$', 'shoutit.tiered_views.user_views.stop_listening_to_user'),
                       url(r'^xhr/user/(\w+)/(listeners|listening)/(?:(\w+)/)?(?:(\w+)/)?$',
                           'shoutit.tiered_views.user_views.user_stats'),

                       url(r'^xhr/tag/$', 'shoutit.tiered_views.tag_views.search_tag'),
                       url(r'^xhr/tag/([^/]+)/start_listening/$', 'shoutit.tiered_views.tag_views.start_listening_to_tag'),
                       url(r'^xhr/tag/([^/]+)/stop_listening/$', 'shoutit.tiered_views.tag_views.stop_listening_to_tag'),
                       url(r'^xhr/tag/([^/]+)/listeners/$', 'shoutit.tiered_views.tag_views.tag_stats'),

                       url(r'^xhr/user/(?P<username>[\.\w-]+)/picture/(?:(?P<size>\d+)/)?$',
                           'shoutit.tiered_views.general_views.profile_picture'
                           , {'profile_type': 'user'}),
                       url(r'^xhr/tag/(?P<tag_name>[a-z0-9-]+)/picture/(?:(?P<size>\d+)/)?$',
                           'shoutit.tiered_views.general_views.profile_picture'
                           , {'profile_type': 'tag'}),

                       url(r'^(?:xhr/)?image/([-\w]+)(?:/(\d+))?/(?:i\.png)?$',
                           'shoutit.tiered_views.general_views.stored_image'),

                       url(r'^xhr/top_tags/$', 'shoutit.tiered_views.tag_views.top_tags'),


                       url(r'^xhr/hovercard/$', 'shoutit.tiered_views.general_views.hovercard'),
                       url(r'^xhr/shout/nearby/$', 'shoutit.tiered_views.shout_views.nearby_shouts'),
                       url(r'^xhr/loadShout/([-\w]+)/$', 'shoutit.tiered_views.shout_views.load_shout'),
                       url(r'^xhr/update_location/$', 'shoutit.tiered_views.user_views.update_user_location'),
                       url(r'^xhr/setTagParent/$', 'shoutit.tiered_views.tag_views.set_tag_parent'),

                       url(r'^sts/$', 'shoutit.tiered_views.general_views.admin_stats'),

                       url(r'^reactivate/$', 'shoutit.tiered_views.user_views.resend_activation'),
                       url(r'^xhr/reactivate/$', 'shoutit.tiered_views.user_views.resend_activation'),
                       url(r'^favicon\.ico$', RedirectView.as_view(url='static/img/icon.png')),
                       url(r'^robots\.txt$', TemplateView.as_view(template_name='robots.txt', content_type='text/plain')),
                       url(r'^googlebc700f17ba42dd9f\.html$',
                           TemplateView.as_view(template_name='googlebc700f17ba42dd9f.html', content_type='text/plain')),

                       url(r'^activate/$', 'shoutit.tiered_views.user_views.activate_user'),
                       url(r'^xhr/activate/$', 'shoutit.tiered_views.user_views.activate_user'),

                       url(r'^confirm_business/', 'shoutit.tiered_views.business_views.confirm_business'),
                       url(r'^xhr/confirm_business/', 'shoutit.tiered_views.business_views.confirm_business'),

                       url(r'^create_tiny_business/', 'shoutit.tiered_views.business_views.create_tiny_business'),
                       url(r'^xhr/create_tiny_business/', 'shoutit.tiered_views.business_views.create_tiny_business'),

                       url(r'^modal/(?:(\w+)/)?$', 'shoutit.tiered_views.general_views.modal'),

                       url(r'^(?:xhr/)?shout_deal/', 'shoutit.tiered_views.deal_views.shout_deal'),
                       url(r'^(?:xhr/)?close_deal/([a-zA-z0-9]+)/', 'shoutit.tiered_views.deal_views.close_deal'),
                       url(r'^(?:xhr/)?valid_voucher/', 'shoutit.tiered_views.deal_views.is_voucher_valid'),
                       url(r'^(?:xhr/)?invalidate_voucher/', 'shoutit.tiered_views.deal_views.invalidate_voucher'),
                       url(r'^(?:xhr/)?deal/([a-zA-z0-9]+)/$', 'shoutit.tiered_views.deal_views.view_deal'),
                       url(r'^(?:xhr/)?deals/$', 'shoutit.tiered_views.deal_views.view_deals'),
                       url(r'^xhr/deals_stream/(\w+)/(?:(\d+)/)?$', 'shoutit.tiered_views.deal_views.deals_stream'),

                       url(r'^set_perma/$', 'shoutit.tiered_views.general_views.set_perma'),

                       # Facebook Stuff
                       url(r'^fb_auth/$', 'shoutit.tiered_views.user_views.fb_auth'),
                       url(r'^fb/connect/$', 'shoutit.tiered_views.fb_views.fb_connect'),
                       url(r'^fb/share/$', 'shoutit.tiered_views.fb_views.fb_share'),
                       url(r'^fb/tab/$', 'shoutit.tiered_views.fb_views.fb_tab'),
                       url(r'^fb/tab_edit/$', 'shoutit.tiered_views.fb_views.fb_tab_edit'),
                       url(r'^fb/comp/(\d+)/$', 'shoutit.tiered_views.fb_views.fb_comp'),
                       url(r'^fb/comp_page/(\d+)/$', 'shoutit.tiered_views.fb_views.fb_comp_page'),
                       url(r'^fb/comp_add/(\d+)/(\w+)/(\w+)/(\w+)/$', 'shoutit.tiered_views.fb_views.fb_comp_add'),

                       # Google Stuff
                       url(r'^gplus_auth/$', 'shoutit.tiered_views.user_views.gplus_auth'),

                       url(r'^set_language/', 'shoutit.tiered_views.general_views.set_language'),
                       url(r'^jsi18n/$', 'django.views.i18n.javascript_catalog', {'packages': ('shoutit',)}),

                       url(r'^(?:bad-|good-)?experience/([-\w]+)/', 'shoutit.tiered_views.experience_views.view_experience'),
                       url(r'^xhr/experiences_stream/(\w+)/(?:(\d+)/)?$', 'shoutit.tiered_views.experience_views.experiences_stream'),
                       url(r'^xhr/post_experience/(?:(\w+)/)?$', 'shoutit.tiered_views.experience_views.post_exp'),
                       url(r'^xhr/share_experience/([-\w]+)/$', 'shoutit.tiered_views.experience_views.share_experience'),
                       url(r'^xhr/edit_experience/([-\w]+)/$', 'shoutit.tiered_views.experience_views.edit_experience'),
                       url(r'^xhr/users_shared_experience/([-\w]+)/$',
                           'shoutit.tiered_views.experience_views.users_shared_experience'),

                       url(r'^xhr/comment_on_post/([-\w]+)/$', 'shoutit.tiered_views.comment_views.comment_on_post'),
                       url(r'^xhr/post_comments/([-\w]+)/$', 'shoutit.tiered_views.comment_views.post_comments'),
                       url(r'^xhr/delete_comment/([-\w]+)/$', 'shoutit.tiered_views.comment_views.delete_comment'),

                       url(r'^xhr/gallery_items_stream/(\w+)/(?:(\d+)/)?$', 'shoutit.tiered_views.gallery_views.galleryItems_stream'),
                       url(r'^xhr/add_gallery_item/([-\w]+)/$', 'shoutit.tiered_views.gallery_views.add_gallery_item'),
                       url(r'^xhr/delete_gallery_item/([-\w]+)/$', 'shoutit.tiered_views.gallery_views.delete_gallery_item'),
                       url(r'^xhr/shout_item/([-\w]+)/$', 'shoutit.tiered_views.gallery_views.shout_item'),
                       url(r'^xhr/edit_item/([-\w]+)/$', 'shoutit.tiered_views.gallery_views.edit_item'),

                       url(r'^xhr/report/(\d+)/([-\w]+)/$', 'shoutit.tiered_views.report_views.report'),
                       url(r'^xhr/delete_comment/([-\w]+)/$', 'shoutit.tiered_views.comment_views.delete_comment'),
                       url(r'^paypal/$', 'shoutit.tiered_views.deal_views.paypal'),
                       url(r'^paypal_return/$', 'shoutit.tiered_views.payment_views.pdt'),
                       url(r'^cpsp_(\w+)/$', 'shoutit.tiered_views.deal_views.cpsp_action'),


                       url(r'^contact-import/$', 'shoutit.tiered_views.user_views.import_contacts', name='import_contacts'),
                       url(r'^(?:xhr/)?send_invitations/$', 'shoutit.tiered_views.user_views.send_invitations'),

                       # user
                       url(r'^([\w.]+)$', 'shoutit.tiered_views.user_views.user_profile'),

                       # url(r'^([abcdefghklmnopqrstuvwxyzABCDEFGHKLMNPQRSTUVWXYZ23456789]+)/$',
                       #     'shoutit.tiered_views.user_views.activate_modal'),

)

# urlpatterns += patterns('',
#	url(r'^admin/django-lean/', include('django_lean.experiments.admin_urls')),
#	url(r'^django-lean/', include('django_lean.experiments.urls')),
#)