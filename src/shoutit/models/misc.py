from __future__ import unicode_literals
import uuid

from django.db import models
from django.conf import settings
from common.constants import TOKEN_TYPE_EMAIL, TokenType

from shoutit.models.base import UUIDModel, LocationMixin
AUTH_USER_MODEL = getattr(settings, 'AUTH_USER_MODEL')


class PredefinedCity(UUIDModel):
    city = models.CharField(max_length=200, default='', blank=True, db_index=True, unique=True)
    city_encoded = models.CharField(max_length=200, default='', blank=True, db_index=True, unique=True)
    country = models.CharField(max_length=2, default='', blank=True, db_index=True)
    latitude = models.FloatField(default=0.0)
    longitude = models.FloatField(default=0.0)
    approved = models.BooleanField(default=False)

    def __str__(self):
        return unicode(self.country + ':' + self.city)


def generate_email_confirm_token():
    return str(uuid.uuid4().hex) + str(uuid.uuid4().hex)


class ConfirmToken(UUIDModel):
    type = models.IntegerField(default=TOKEN_TYPE_EMAIL.value)
    user = models.ForeignKey(AUTH_USER_MODEL, related_name="confirmation_tokens")
    token = models.CharField(max_length=64, db_index=True, unique=True, default=generate_email_confirm_token)
    email = models.EmailField(blank=True, null=True)
    is_disabled = models.BooleanField(default=False)

    def __str__(self):
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
#     user = models.ForeignKey(AUTH_USER_MODEL, related_name='Documents', null=True, blank=True)
#     File = models.CharField(max_length=1024)
#     type = models.IntegerField()
#
#     def __str__(self):
#         return "(" + unicode(self.pk) + ") " + unicode(self.File)
