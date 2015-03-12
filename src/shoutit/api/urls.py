from django.conf.urls import include, patterns, url

from shoutit.tiered_views import general_views, shout_views


urlpatterns = patterns('',

                       # sss
                       url(r'^sss4/$', shout_views.shout_sss4),

                       # inbound
                       url(r'^in/$', shout_views.inbound_email),

                       # error
                       url(r'^error/$', general_views.fake_error),
)

urlpatterns += [
    url(r'^auth/', include('rest_framework.urls', namespace='rest_framework')),
    url(r'^v2/', include('shoutit.api.v2.urls', namespace='v2')),
]
