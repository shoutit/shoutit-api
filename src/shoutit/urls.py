from __future__ import unicode_literals
from django.conf.urls import include, url
from django.views.generic import RedirectView
from django.contrib import admin
from django.conf import settings
from shoutit.tiered_views import general_views

urlpatterns = [
    # current api root
    url(r'^$', RedirectView.as_view(url='/v2/', permanent=False)),

    # admin
    url(r'^grappelli/', include('grappelli.urls')),
    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
    url(r'^admin/', include(admin.site.urls)),

    # return fake error
    url(r'^error$', general_views.fake_error),

    # drf api auth
    url(r'^auth/', include('rest_framework.urls', namespace='rest_framework')),

    # api v2
    url(r'^v2/', include('shoutit.api.v2.urls', namespace='v2')),

    # django-rq
    (r'^rq/', include('django_rq.urls')),

    # todo: move to web
    url(r'^favicon\.ico$',
        RedirectView.as_view(url=settings.STATIC_URL + 'img/icon.png', permanent=True)),
    url(r'^robots\.txt$',
        RedirectView.as_view(url=settings.STATIC_URL + 'robots.txt', permanent=True)),

    # todo: 2nd release concepts!
    # Business
    # url(r'^(?:xhr/)?recover_business_activation/$', 'shoutit.tiered_views.business_views.recover_activation'),
    # url(r'^^(?:xhr/)?bsignup/(?:([-\w]+)/)?$', 'shoutit.tiered_views.business_views.signup'),
    # url(r'^^(?:xhr/)?subscribe/$', 'shoutit.tiered_views.business_views.subscribe'),
    # url(r'^^(?:xhr/)?btempsignup/(?:([-\w]+)/)?$', 'shoutit.tiered_views.business_views.signup_temp'),
    # url(r'^(?:xhr/)?user/(\w+)/editBusinessProfile/$', 'shoutit.tiered_views.business_views.business_edit_profile'),
    # url(r'^confirm_business/', 'shoutit.tiered_views.business_views.confirm_business'),
    # url(r'^xhr/confirm_business/', 'shoutit.tiered_views.business_views.confirm_business'),
    # url(r'^create_tiny_business/', 'shoutit.tiered_views.business_views.create_tiny_business'),
    # url(r'^xhr/create_tiny_business/', 'shoutit.tiered_views.business_views.create_tiny_business'),

    # Experience
    # url(r'^(?:bad-|good-)?experience/([-\w]+)/', 'shoutit.tiered_views.experience_views.view_experience'),
    # url(r'^xhr/experiences_stream/(\w+)/(?:(\d+)/)?$', 'shoutit.tiered_views.experience_views.experiences_stream'),
    # url(r'^xhr/post_experience/(?:(\w+)/)?$', 'shoutit.tiered_views.experience_views.post_exp'),
    # url(r'^xhr/share_experience/([-\w]+)/$', 'shoutit.tiered_views.experience_views.share_experience'),
    # url(r'^xhr/edit_experience/([-\w]+)/$', 'shoutit.tiered_views.experience_views.edit_experience'),
    # url(r'^xhsetr/users_shared_experience/([-\w]+)/$', 'shoutit.tiered_views.experience_views.users_shared_experience'),

    # Comment
    # url(r'^xhr/comment_on_post/([-\w]+)/$', 'shoutit.tiered_views.comment_views.comment_on_post'),
    # url(r'^xhr/post_comments/([-\w]+)/$', 'shoutit.tiered_views.comment_views.post_comments'),
    # url(r'^xhr/delete_comment/([-\w]+)/$', 'shoutit.tiered_views.comment_views.delete_comment'),
    # url(r'^xhr/delete_comment/([-\w]+)/$', 'shoutit.tiered_views.comment_views.delete_comment'),

    # Deals
    # url(r'^(?:xhr/)?shout_deal/', 'shoutit.tiered_views.deal_views.shout_deal'),
    # url(r'^(?:xhr/)?close_deal/([a-zA-z0-9]+)/', 'shoutit.tiered_views.deal_views.close_deal'),
    # url(r'^(?:xhr/)?valid_voucher/', 'shoutit.tiered_views.deal_views.is_voucher_valid'),
    # url(r'^(?:xhr/)?invalidate_voucher/', 'shoutit.tiered_views.deal_views.invalidate_voucher'),
    # url(r'^(?:xhr/)?deal/([a-zA-z0-9]+)/$', 'shoutit.tiered_views.deal_views.view_deal'),
    # url(r'^(?:xhr/)?deals/$', 'shoutit.tiered_views.deal_views.view_deals'),
    # url(r'^xhr/deals_stream/(\w+)/(?:(\d+)/)?$', 'shoutit.tiered_views.deal_views.deals_stream'),

    # Paypal
    # url(r'^paypal/$', 'shoutit.tiered_views.deal_views.paypal'),
    # url(r'^paypal_return/$', 'shoutit.tiered_views.payment_views.pdt'),
    # url(r'^cpsp_(\w+)/$', 'shoutit.tiered_views.deal_views.cpsp_action'),
]

# serving static files while developing locally using gunicorn
if settings.GUNICORN and settings.LOCAL:
    from django.contrib.staticfiles.urls import staticfiles_urlpatterns

    urlpatterns += staticfiles_urlpatterns()
