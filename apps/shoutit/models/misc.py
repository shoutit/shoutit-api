from datetime import timedelta, datetime
from django.db import models
from apps.shoutit.models.base import UUIDModel
from django.conf import settings
AUTH_USER_MODEL = getattr(settings, 'AUTH_USER_MODEL')


class PredefinedCity(UUIDModel):
    City = models.CharField(max_length=200, default='', blank=True, db_index=True, unique=True)
    city_encoded = models.CharField(max_length=200, default='', blank=True, db_index=True, unique=True)
    Country = models.CharField(max_length=2, default='', blank=True, db_index=True)
    Latitude = models.FloatField(default=0.0)
    Longitude = models.FloatField(default=0.0)
    Approved = models.BooleanField(default=False)

    def __unicode__(self):
        return unicode(self.Country + ':' + self.City)


class StoredFile(UUIDModel):
    user = models.ForeignKey(AUTH_USER_MODEL, related_name='Documents', null=True, blank=True)
    File = models.CharField(max_length=1024)
    Type = models.IntegerField()

    def __unicode__(self):
        return "(" + unicode(self.pk) + ") " + unicode(self.File)


class ConfirmToken(UUIDModel):
    Token = models.CharField(max_length=24, db_index=True, unique=True)
    user = models.ForeignKey(AUTH_USER_MODEL, related_name="Tokens")
    Type = models.IntegerField(default=0)
    DateCreated = models.DateField(auto_now_add=True)
    Email = models.CharField(max_length=128, blank=True)
    IsDisabled = models.BooleanField(default=False, null=False)

    def __unicode__(self):
        return unicode(self.pk) + ": " + unicode(self.user) + "::" + self.Token

    def disable(self):
        self.IsDisabled = True
        self.save()

    @staticmethod
    def getToken(token, get_disabled=True, case_sensitive=True):
        today = datetime.today()
        days = timedelta(days=int(settings.MAX_REG_DAYS))
        begin = today - days
        if case_sensitive:
            t = ConfirmToken.objects.filter(Token__exact=token, DateCreated__gte=begin, DateCreated__lte=today)
        else:
            t = ConfirmToken.objects.filter(Token__iexact=token, DateCreated__gte=begin, DateCreated__lte=today)
        if not get_disabled:
            t = t.filter(IsDisabled=False)
        t = t.select_related(depth=1)
        if len(t) > 0:
            return t[0]
        else:
            return None


class FbContest(UUIDModel):
    ContestId = models.IntegerField(db_index=True)
    user = models.ForeignKey(AUTH_USER_MODEL, related_name='Contest_1')
    FbId = models.CharField(max_length=24, db_index=True)
    ShareId = models.CharField(max_length=50, null=True, blank=True, default=None)


class SharedLocation(UUIDModel):
    city = models.CharField(max_length=200)
    country = models.CharField(max_length=2)
    latitude = models.FloatField()
    longitude = models.FloatField()

