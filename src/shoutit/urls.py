from __future__ import unicode_literals

from django.conf import settings
from django.conf.urls import include, url
from django.contrib import admin
from django.views.generic import RedirectView

urlpatterns = [
    # Admin
    url(r'^grappelli/', include('grappelli.urls')),
    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
    url(r'^admin/rq/', include('django_rq.urls')),
    url(r'^admin/', include(admin.site.urls)),

    # Current API root
    url(r'^$', RedirectView.as_view(url='/v3/', permanent=False)),

    # API v2
    url(r'^v2/', include('shoutit.api.v2.urls', namespace='v2')),

    # API v3
    url(r'^v3/', include('shoutit.api.v3.urls', namespace='v3')),

    # API Docs
    url(r'^docs/', include('rest_framework_swagger.urls')),

    # DRF API Auth
    url(r'^auth/', include('rest_framework.urls', namespace='rest_framework')),

    # Heartbeat
    url(r'^heartbeat', include('heartbeat.urls')),
]

# serving static files while developing locally using gunicorn
if settings.GUNICORN and settings.LOCAL:
    from django.contrib.staticfiles.urls import staticfiles_urlpatterns

    urlpatterns += staticfiles_urlpatterns()
