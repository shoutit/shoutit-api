from __future__ import unicode_literals

from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.conf import settings

from common.constants import BUSINESS_SOURCE_TYPE_NONE, BUSINESS_CONFIRMATION_STATUS_WAITING
from shoutit.models.base import UUIDModel

AUTH_USER_MODEL = getattr(settings, 'AUTH_USER_MODEL')


class BusinessCategoryManager(models.Manager):
    def get_tuples(self):
        return ((c.pk, c.name) for c in self.all())

    def get_top_level_categories(self):
        return self.filter(Parent=None)


class BusinessCategory(UUIDModel):
    name = models.CharField(max_length=1024, db_index=True, null=False)
    Source = models.IntegerField(default=BUSINESS_SOURCE_TYPE_NONE.value)
    SourceID = models.CharField(max_length=128, blank=True)
    Parent = models.ForeignKey('self', null=True, blank=True, default=None, related_name='children')

    objects = BusinessCategoryManager()

    def __unicode__(self):
        return self.PrintHierarchy()

    def PrintHierarchy(self):
        return unicode('%s > %s' % (self.Parent.PrintHierarchy(), self.name)) if self.Parent else unicode(self.name)


class Business(UUIDModel):
    user = models.OneToOneField(AUTH_USER_MODEL, related_name='business', db_index=True)

    name = models.CharField(max_length=1024, db_index=True, null=False)
    Category = models.ForeignKey('shoutit.BusinessCategory', null=True, blank=True, on_delete=models.SET_NULL)

    image = models.CharField(max_length=1024, null=True, blank=True)
    About = models.TextField(null=True, blank=True, max_length=512, default='')
    Phone = models.CharField(unique=True, null=True, blank=True, max_length=20)
    Website = models.URLField(max_length=1024, null=True, blank=True)

    country = models.CharField(max_length=2, db_index=True, null=True, blank=True)
    city = models.CharField(max_length=200, db_index=True, null=True, blank=True)
    latitude = models.FloatField(default=0.0)
    longitude = models.FloatField(default=0.0)
    address = models.CharField(max_length=200, db_index=True, null=True, blank=True)

    LastToken = models.ForeignKey('shoutit.ConfirmToken', null=True, blank=True, default=None, on_delete=models.SET_NULL)

    Confirmed = models.BooleanField(default=False)

    def __unicode__(self):
        return '[BP_%s | %s | %s]' % (unicode(self.pk), unicode(self.name), unicode(self.user))

    # def __getattribute__(self, name):
    #     if name in ['username', 'first_name', 'last_name', 'email', 'tagsCreated', 'Shouts', 'get_full_name', 'is_active']:
    #         return getattr(self.user, name)
    #     else:
    #         return object.__getattribute__(self, name)
    #
    # def __setattr__(self, name, value):
    #     if name in ['username', 'first_name', 'last_name', 'email', 'tagsCreated', 'Shouts', 'get_full_name', 'is_active']:
    #         setattr(self.user, name, value)
    #     else:
    #         object.__setattr__(self, name, value)

    @property
    def bio(self):
        return self.About

    @bio.setter
    def bio(self, value):
        self.About = value

    @property
    def name(self):
        return self.name

    def has_source(self):
        try:
            if self.Source:
                return True
            else:
                return False
        except ObjectDoesNotExist:
            return False


class BusinessCreateApplication(UUIDModel):
    user = models.ForeignKey(AUTH_USER_MODEL, related_name='BusinessCreateApplication', null=True, blank=True, on_delete=models.SET_NULL)
    business = models.ForeignKey('shoutit.Business', related_name='UserApplications', null=True, blank=True, on_delete=models.SET_NULL)

    name = models.CharField(max_length=1024, db_index=True, null=True, blank=True)
    Category = models.ForeignKey('shoutit.BusinessCategory', null=True, blank=True, on_delete=models.SET_NULL)

    image = models.CharField(max_length=1024, null=True, blank=True)
    About = models.TextField(null=True, blank=True, max_length=512, default='')
    Phone = models.CharField(null=True, blank=True, max_length=20)
    Website = models.URLField(max_length=1024, null=True, blank=True)

    longitude = models.FloatField(default=0.0)
    latitude = models.FloatField(default=0.0)
    country = models.CharField(max_length=2, db_index=True, null=True, blank=True)
    city = models.CharField(max_length=200, db_index=True, null=True, blank=True)
    address = models.CharField(max_length=200, db_index=True, null=True, blank=True)

    LastToken = models.ForeignKey('shoutit.ConfirmToken', null=True, blank=True, default=None, on_delete=models.SET_NULL)
    DateApplied = models.DateField(auto_now_add=True)

    Status = models.IntegerField(default=int(BUSINESS_CONFIRMATION_STATUS_WAITING), db_index=True)


class BusinessSource(UUIDModel):
    business = models.OneToOneField('shoutit.Business', related_name="Source")
    Source = models.IntegerField(default=BUSINESS_SOURCE_TYPE_NONE.value)
    SourceID = models.CharField(max_length=128, blank=True)


class BusinessConfirmation(UUIDModel):
    user = models.ForeignKey(AUTH_USER_MODEL, related_name='BusinessConfirmations')
    Files = models.ManyToManyField('shoutit.StoredFile', related_name='Confirmation')
    DateSent = models.DateTimeField(auto_now_add=True)
