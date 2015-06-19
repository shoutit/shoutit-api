from __future__ import unicode_literals
import uuid

from django.db import models
from django.conf import settings
from common.constants import TOKEN_TYPE_EMAIL, TokenType

from shoutit.models.base import UUIDModel, LocationMixin

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
        cities = PredefinedCity.objects.filter(country=self.country).exclude(id=self.id)\
            .extra(select=distance).values('id', 'distance')
        cities = list(cities)
        cities.sort(key=lambda x: x['distance'])
        ids = [c['id'] for c in cities if float(c['distance']) < dist_km][:max_cities]
        return PredefinedCity.objects.filter(id__in=ids)


def generate_email_confirm_token():
    return str(uuid.uuid4().hex) + str(uuid.uuid4().hex)


class ConfirmToken(UUIDModel):
    type = models.IntegerField(default=TOKEN_TYPE_EMAIL.value)
    user = models.ForeignKey(AUTH_USER_MODEL, related_name="confirmation_tokens")
    token = models.CharField(max_length=64, db_index=True, unique=True,
                             default=generate_email_confirm_token)
    email = models.EmailField(blank=True, null=True)
    is_disabled = models.BooleanField(default=False)

    def __unicode__(self):
        return "{}: {}: {}".format(self.type_name, self.user, self.token)

    @property
    def type_name(self):
        return TokenType.values[self.type]

    def disable(self):
        self.is_disabled = True
        self.save()


class SharedLocation(LocationMixin, UUIDModel):
    pass


# class StoredFile(UUIDModel):
# user = models.ForeignKey(AUTH_USER_MODEL, related_name='Documents', null=True, blank=True)
#     File = models.CharField(max_length=1024)
#     type = models.IntegerField()
#
#     def __unicode__(self):
#         return "(" + unicode(self.pk) + ") " + unicode(self.File)
