from django.conf.urls import patterns, include, url
from django.views.generic import RedirectView
from django.contrib import admin
from django.conf import settings
from shoutit.tiered_views import shout_views, general_views

urlpatterns = patterns('',
                       # admin
                       url(r'^grappelli/', include('grappelli.urls')),
                       url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
                       url(r'^admin/', include(admin.site.urls)),

                       # sss
                       url(r'^sss4$', shout_views.shout_sss4),

                       # inbound
                       url(r'^in$', shout_views.inbound_email),

                       # return fake error
                       url(r'^error$', general_views.fake_error),

                       # drf api auth
                       url(r'^auth/', include('rest_framework.urls', namespace='rest_framework')),

                       # api v2
                       url(r'^v2/', include('shoutit.api.v2.urls', namespace='v2')),

                       # django-rq
                       (r'^rq/', include('django_rq.urls')),

                       # todo: move to web
                       url(r'^favicon\.ico$', RedirectView.as_view(url=settings.STATIC_URL + 'img/icon.png', permanent=True)),
                       url(r'^robots\.txt$', RedirectView.as_view(url=settings.STATIC_URL + 'robots.txt', permanent=True)),
                       url(r'^googlebc700f17ba42dd9f\.html$', RedirectView.as_view(url=settings.STATIC_URL + 'googlebc700f17ba42dd9f.html',
                                                                                   permanent=True)),
                       # todo: remove everything below!
                       # Old website
                       url(r'^$', RedirectView.as_view(url='/v2/')),
                       url(r'^(requests|offers|experiences)/$', 'shoutit.tiered_views.general_views.index', ),

                       url(r'^tos/$', 'shoutit.tiered_views.general_views.tos'),
                       url(r'^tos/$', 'shoutit.tiered_views.general_views.tos'),
                       url(r'^privacy/$', 'shoutit.tiered_views.general_views.privacy'),
                       url(r'^rules/$', 'shoutit.tiered_views.general_views.rules'),
                       url(r'^learnmore/$', 'shoutit.tiered_views.general_views.learnmore'),

                       url(r'^xhr/live_events/$', 'shoutit.tiered_views.general_views.live_events'),
                       url(r'^xhr/delete_event/([-\w]+)/$', 'shoutit.tiered_views.general_views.delete_event'),

                       url(r'^(?:xhr/)?signup/$', 'shoutit.tiered_views.user_views.signup'),
                       url(r'^(?:xhr/)?signin/$', 'shoutit.tiered_views.user_views.signin'),
                       url(r'^(?:xhr/)?signout/$', 'shoutit.tiered_views.user_views.signout'),
                       url(r'^(?:xhr/)?recover/$', 'shoutit.tiered_views.user_views.recover'),
                       url(r'^(?:xhr/)?recover_business_activation/$', 'shoutit.tiered_views.business_views.recover_activation'),
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
                       url(r'^xhr/user/(\w+)/activities_stream/?$', 'shoutit.tiered_views.user_views.activities_stream'),
                       url(r'^(?:xhr/)?user/(\w+)/editProfile/$', 'shoutit.tiered_views.user_views.user_edit_profile'),
                       url(r'^(?:xhr/)?user/(\w+)/editBusinessProfile/$', 'shoutit.tiered_views.business_views.business_edit_profile'),


                       url(r'^(?:xhr/)?reply/([-\w]+)/(?:([-\w]+)/)?$', 'shoutit.tiered_views.message_views.send_message'),
                       url(r'^xhr/delete_conversation/([-\w]+)/$', 'shoutit.tiered_views.message_views.delete_conversation'),
                       url(r'^xhr/delete_message/([-\w]+)/([-\w]+)/$', 'shoutit.tiered_views.message_views.delete_message'),
                       url(r'^xhr/getHtmlMessage/$', 'shoutit.tiered_views.message_views.get_html_message'),
                       url(r'^messages/$', 'shoutit.tiered_views.message_views.read_conversations'),
                       url(r'^(?:xhr/)?messages/stream/$', 'shoutit.tiered_views.message_views.read_conversations_stream'),
                       url(r'^(?:xhr/)?messages/([-\w]+)/$', 'shoutit.tiered_views.message_views.read_conversation'),
                       url(r'^xhr/message/([-\w]+)/read/$', 'shoutit.tiered_views.message_views.mark_message_as_read'),

                       url(r'^notifications/$', 'shoutit.tiered_views.realtime_views.notifications'),
                       url(r'^xhr/notifications/count/$', 'shoutit.tiered_views.realtime_views.notifications_count'),

                       # XHR
                       url(r'^xhr/user/$', 'shoutit.tiered_views.user_views.search_user'),
                       url(r'^xhr/user/(\w+)/start_listening/$', 'shoutit.tiered_views.user_views.start_listening_to_user'),
                       url(r'^xhr/user/(\w+)/stop_listening/$', 'shoutit.tiered_views.user_views.stop_listening_to_user'),
                       url(r'^xhr/user/(\w+)/(listeners|listening)/(?:(\w+)/)?(?:(\w+)/)?$', 'shoutit.tiered_views.user_views.user_stats'),

                       url(r'^xhr/tag/$', 'shoutit.tiered_views.tag_views.search_tag'),
                       url(r'^xhr/tag/([^/]+)/start_listening/$', 'shoutit.tiered_views.tag_views.start_listening_to_tag'),
                       url(r'^xhr/tag/([^/]+)/stop_listening/$', 'shoutit.tiered_views.tag_views.stop_listening_to_tag'),
                       url(r'^xhr/tag/([^/]+)/listeners/$', 'shoutit.tiered_views.tag_views.tag_stats'),
                       url(r'^xhr/top_tags/$', 'shoutit.tiered_views.tag_views.top_tags'),

                       url(r'^xhr/shout/nearby/$', 'shoutit.tiered_views.shout_views.nearby_shouts'),
                       url(r'^xhr/loadShout/([-\w]+)/$', 'shoutit.tiered_views.shout_views.load_shout'),
                       url(r'^xhr/update_location/$', 'shoutit.tiered_views.user_views.update_user_location'),
                       url(r'^xhr/setTagParent/$', 'shoutit.tiered_views.tag_views.set_tag_parent'),

                       url(r'^reactivate/$', 'shoutit.tiered_views.user_views.resend_activation'),
                       url(r'^xhr/reactivate/$', 'shoutit.tiered_views.user_views.resend_activation'),
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

                       url(r'^jsi18n/$', 'django.views.i18n.javascript_catalog', {'packages': ('shoutit',)}),

                       url(r'^(?:bad-|good-)?experience/([-\w]+)/', 'shoutit.tiered_views.experience_views.view_experience'),
                       url(r'^xhr/experiences_stream/(\w+)/(?:(\d+)/)?$', 'shoutit.tiered_views.experience_views.experiences_stream'),
                       url(r'^xhr/post_experience/(?:(\w+)/)?$', 'shoutit.tiered_views.experience_views.post_exp'),
                       url(r'^xhr/share_experience/([-\w]+)/$', 'shoutit.tiered_views.experience_views.share_experience'),
                       url(r'^xhr/edit_experience/([-\w]+)/$', 'shoutit.tiered_views.experience_views.edit_experience'),
                       url(r'^xhr/users_shared_experience/([-\w]+)/$', 'shoutit.tiered_views.experience_views.users_shared_experience'),

                       url(r'^xhr/comment_on_post/([-\w]+)/$', 'shoutit.tiered_views.comment_views.comment_on_post'),
                       url(r'^xhr/post_comments/([-\w]+)/$', 'shoutit.tiered_views.comment_views.post_comments'),
                       url(r'^xhr/delete_comment/([-\w]+)/$', 'shoutit.tiered_views.comment_views.delete_comment'),

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
                       # 'shoutit.tiered_views.user_views.activate_modal'),
)

# serving static files while developing locally using gunicorn
if settings.GUNICORN and settings.LOCAL:
    from django.contrib.staticfiles.urls import staticfiles_urlpatterns

    urlpatterns += staticfiles_urlpatterns()
