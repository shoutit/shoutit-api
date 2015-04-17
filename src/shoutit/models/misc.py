from __future__ import unicode_literals
from datetime import timedelta, datetime

from django.db import models
from django.conf import settings

from shoutit.models.base import UUIDModel, LocationMixin
AUTH_USER_MODEL = getattr(settings, 'AUTH_USER_MODEL')


class PredefinedCity(UUIDModel):
    city = models.CharField(max_length=200, default='', blank=True, db_index=True, unique=True)
    city_encoded = models.CharField(max_length=200, default='', blank=True, db_index=True, unique=True)
    country = models.CharField(max_length=2, default='', blank=True, db_index=True)
    latitude = models.FloatField(default=0.0)
    longitude = models.FloatField(default=0.0)
    Approved = models.BooleanField(default=False)

    def __str__(self):
        return unicode(self.country + ':' + self.city)


class StoredFile(UUIDModel):
    user = models.ForeignKey(AUTH_USER_MODEL, related_name='Documents', null=True, blank=True)
    File = models.CharField(max_length=1024)
    type = models.IntegerField()

    def __str__(self):
        return "(" + unicode(self.pk) + ") " + unicode(self.File)


class ConfirmToken(UUIDModel):
    Token = models.CharField(max_length=24, db_index=True, unique=True)
    user = models.ForeignKey(AUTH_USER_MODEL, related_name="Tokens")
    type = models.IntegerField(default=0)
    Email = models.CharField(max_length=128, blank=True, null=True)
    is_disabled = models.BooleanField(default=False, null=False)

    def __str__(self):
        return unicode(self.pk) + ": " + unicode(self.user) + "::" + self.Token

    def disable(self):
        self.is_disabled = True
        self.save()

    @staticmethod
    def getToken(token, get_disabled=True, case_sensitive=True):
        today = datetime.today()
        days = timedelta(days=int(settings.MAX_REG_DAYS))
        begin = today - days
        if case_sensitive:
            t = ConfirmToken.objects.filter(Token__exact=token, created_at__gte=begin, created_at__lte=today)
        else:
            t = ConfirmToken.objects.filter(Token__iexact=token, created_at__gte=begin, created_at__lte=today)
        if not get_disabled:
            t = t.filter(is_disabled=False)
        if len(t) > 0:
            return t[0]
        else:
            return None


class FbContest(UUIDModel):
    ContestId = models.IntegerField(db_index=True)
    user = models.ForeignKey(AUTH_USER_MODEL, related_name='Contest_1')
    FbId = models.CharField(max_length=24, db_index=True)
    ShareId = models.CharField(max_length=50, null=True, blank=True, default=None)


class SharedLocation(LocationMixin, UUIDModel):
    pass
