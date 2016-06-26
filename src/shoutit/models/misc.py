from __future__ import unicode_literals

import uuid

from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django_rq import job
from elasticsearch import RequestError, ConnectionTimeout, NotFoundError, ConflictError
from elasticsearch_dsl import DocType, String, GeoPoint
from pydash import arrays

from common.constants import TOKEN_TYPE_EMAIL, TokenType, SMSInvitationStatus, SMS_INVITATION_ADDED, DeviceOS
from shoutit.models.base import UUIDModel, LocationMixin
from ..utils import error_logger, debug_logger

AUTH_USER_MODEL = getattr(settings, 'AUTH_USER_MODEL')


class PredefinedCity(UUIDModel, LocationMixin):
    approved = models.BooleanField(default=False)

    class Meta:
        unique_together = ('country', 'postal_code', 'state', 'city')

    def __unicode__(self):
        return unicode(self.country + ':' + self.city)

    def get_cities_within(self, dist_km, max_cities=30):
        distance = {
            'distance': """(6371 * acos( cos( radians(%s) ) * cos( radians( latitude ) ) *
                    cos( radians( longitude ) - radians(%s) ) + sin( radians(%s) ) *
                    sin( radians( latitude ) ) ) )""" % (self.latitude, self.longitude, self.latitude)
        }
        cities = PredefinedCity.objects.filter(country=self.country).exclude(id=self.id).extra(select=distance).values(
            'id', 'distance')
        cities = list(cities)
        cities.sort(key=lambda x: x['distance'])
        ids = [c['id'] for c in cities if float(c['distance']) < dist_km][:max_cities]
        ids = arrays.unique(ids)
        return PredefinedCity.objects.filter(id__in=ids)


def generate_email_confirm_token():
    return str(uuid.uuid4().hex) + str(uuid.uuid4().hex)


class ConfirmToken(UUIDModel):
    type = models.IntegerField(choices=TokenType.choices, default=TOKEN_TYPE_EMAIL.value)
    user = models.ForeignKey(AUTH_USER_MODEL, related_name="confirmation_tokens")
    token = models.CharField(max_length=64, unique=True, default=generate_email_confirm_token)
    email = models.EmailField(blank=True, null=True)
    is_disabled = models.BooleanField(default=False)

    def __unicode__(self):
        return "%s: %s: %s" % (self.get_type_display(), self.user, self.token)

    def disable(self):
        self.is_disabled = True
        self.save()


class SharedLocation(LocationMixin, UUIDModel):
    pass


class GoogleLocation(LocationMixin, UUIDModel):
    geocode_response = models.TextField(max_length=5000)
    is_indexed = models.BooleanField(default=False, db_index=True)

    def __unicode__(self):
        return "%s [%0.6f,%0.6f]: %s, %s" % (self.country, self.latitude, self.longitude, self.state, self.city)

    class Meta:
        unique_together = ('country', 'state', 'city', 'postal_code', 'latitude', 'longitude')


class LocationIndex(DocType):
    source = String(index='not_analyzed')
    location = GeoPoint()
    country = String(index='not_analyzed')
    postal_code = String(index='not_analyzed')
    state = String(index='not_analyzed')
    city = String(index='not_analyzed')
    address = String(index='not_analyzed')

    class Meta:
        index = '%s_location' % settings.ES_BASE_INDEX

    @property
    def location_dict(self):
        return {
            'latitude': self.location['lat'],
            'longitude': self.location['lon'],
            'country': self.country,
            'postal_code': self.postal_code,
            'state': self.state,
            'city': self.city,
            'address': self.address,
        }


# initiate the index if not initiated
try:
    LocationIndex.init()
except RequestError:
    pass
except ConnectionTimeout:
    error_logger.warn("ES Server is down", exc_info=True)


@receiver(post_save, sender=GoogleLocation)
def location_post_save(sender, instance=None, created=False, **kwargs):
    action = 'Created' if created else 'Updated'
    debug_logger.debug('{} {}: {}'.format(action, instance.model_name, instance))
    # save index
    save_location_index(instance, created)


@receiver(post_delete, sender=GoogleLocation)
def location_post_delete(sender, instance=None, created=False, **kwargs):
    debug_logger.debug('Deleted {}: {}'.format(instance.model_name, instance))
    # delete index
    delete_object_index.delay(LocationIndex, instance)


def save_location_index(location=None, created=False, delay=True):
    if delay:
        location = type(location).objects.get(id=location.id)
        return _save_location_index.delay(location, created)
    return _save_location_index(location, created)


@job(settings.RQ_QUEUE)
def _save_location_index(location=None, created=False):
    try:
        if created:
            raise NotFoundError()
        location_index = LocationIndex.get(location.pk)
    except NotFoundError:
        location_index = LocationIndex()
        location_index._id = location.pk
        location_index.source = type(location).__name__
    location_index = location_index_from_location(location, location_index)
    if location_index.save():
        debug_logger.debug('Created LocationIndex: %s' % location)
    else:
        debug_logger.debug('Updated LocationIndex: %s' % location)
    # Update the location object without dispatching signals
    location._meta.model.objects.filter(id=location.id).update(is_indexed=True)


def location_index_from_location(location, location_index=None):
    if location_index is None:
        location_index = LocationIndex()
        location_index._id = location.pk
        location_index.source = type(location).__name__
    location_index.location = {
        'lat': location.latitude,
        'lon': location.longitude
    }
    location_index.country = location.country
    location_index.postal_code = location.postal_code
    location_index.state = location.state
    location_index.city = location.city
    location_index.address = location.address
    return location_index


@job(settings.RQ_QUEUE)
def delete_object_index(index_model, obj):
    index_model_name = index_model.__name__
    try:
        object_index = index_model.get(obj.pk)
        object_index.delete()
        debug_logger.debug('Deleted %s: %s' % (index_model_name, obj.pk))
    except NotFoundError:
        debug_logger.debug('%s: %s not found' % (index_model_name, obj.pk))
    except ConflictError:
        debug_logger.debug('%s: %s already deleted' % (index_model_name, obj.pk))


# class StoredFile(UUIDModel):
# user = models.ForeignKey(AUTH_USER_MODEL, related_name='Documents', null=True, blank=True)
#     File = models.CharField(max_length=1024)
#     type = models.IntegerField()
#
#     def __unicode__(self):
#         return "(" + unicode(self.pk) + ") " + unicode(self.File)


class SMSInvitation(UUIDModel):
    user = models.ForeignKey(AUTH_USER_MODEL, related_name="sms_invitation", null=True, blank=True)
    message = models.CharField(max_length=160)
    old_message = models.CharField(max_length=160, default='', blank=True)
    mobile = models.CharField(max_length=20, unique=True)
    status = models.SmallIntegerField(default=SMS_INVITATION_ADDED.value, choices=SMSInvitationStatus.choices)
    country = LocationMixin._meta.get_field("country")

    def __unicode__(self):
        return "%s %s for %s" % (self.country, self.status, self.mobile)


class Device(UUIDModel):
    user = models.ForeignKey(AUTH_USER_MODEL, related_name='devices')
    type = models.SmallIntegerField(choices=DeviceOS.choices, db_index=True)
    api_version = models.CharField(max_length=10, db_index=True)
    push_device = GenericForeignKey('content_type', 'object_id')

    content_type = models.ForeignKey(ContentType, null=True, blank=True)
    object_id = models.IntegerField(null=True, blank=True)

    def __unicode__(self):
        return "%s:%s" % (self.api_version, self.get_type_display())
