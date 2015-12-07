from __future__ import unicode_literals
import uuid

from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.contrib.postgres.fields import ArrayField
from django.core import validators
from django.db import models
from django.utils.translation import ugettext_lazy as _

from common.utils import date_unix
from common.constants import COUNTRY_ISO, COUNTRY_CHOICES


class UUIDModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(verbose_name=_("Creation time"), auto_now_add=True, null=True)
    modified_at = models.DateTimeField(verbose_name=_("Modification time"), auto_now=True, null=True)

    class Meta:
        abstract = True

    @classmethod
    def create(cls, save=True, **kwargs):
        """
        Creates a new object with the given kwargs, saving it to the database and returning the created object.
        """
        obj = cls(**kwargs)
        if save:
            obj.save()
        return obj

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        if not (force_insert or force_update):
            self.full_clean()
        super(UUIDModel, self).save(force_insert, force_update, using=None, update_fields=None)

    def update(self, **kwargs):
        field_names = self._meta.get_all_field_names()
        update_fields = []
        for k in kwargs.keys():
            if k in field_names:
                setattr(self, k, kwargs[k])
                update_fields.append(k)
        self.save(update_fields=update_fields)
        return self

    @property
    def pk(self):
        return str(self.id).lower()

    @property
    def created_at_unix(self):
        return date_unix(self.created_at)

    @property
    def modified_at_unix(self):
        return date_unix(self.modified_at)

    @property
    def model_name(self):
        return type(self).__name__


class AttachedObjectMixinManager(models.Manager):
    def with_attached_object(self, attached_object):
        ct = ContentType.objects.get_for_model(attached_object)
        queryset = super(AttachedObjectMixinManager, self).get_queryset()
        return queryset.filter(content_type=ct, object_id=attached_object.id)


class AttachedObjectMixin(models.Model):
    content_type = models.ForeignKey(ContentType, null=True, blank=True)
    object_id = models.UUIDField(null=True, blank=True)
    attached_object = GenericForeignKey('content_type', 'object_id')

    objects = AttachedObjectMixinManager()

    class Meta:
        abstract = True


class APIModelMixin(object):
    @property
    def web_url(self):
        name = self.__class__.__name__.lower()
        lookups = {
            # class: ('url part', 'lookup')
            'user': ('user', 'username'),
            'tag': ('tag', 'name'),
            'shout': ('shout', 'pk'),
        }
        lookup = getattr(self, lookups.get(name, (name, 'pk'))[1], '')
        return "{}{}/{}".format(settings.SITE_LINK, name, lookup)


class AbstractLocationMixin(models.Model):
    latitude = models.FloatField(
        default=0, validators=[validators.MaxValueValidator(90), validators.MinValueValidator(-90)])
    longitude = models.FloatField(
        default=0, validators=[validators.MaxValueValidator(180), validators.MinValueValidator(-180)])
    address = models.CharField(max_length=200, blank=True)

    class Meta:
        abstract = True

    @property
    def is_zero_coord(self):
        return self.latitude == 0 and self.longitude == 0


class NamedLocationMixin(models.Model):
    country = models.CharField(max_length=2, blank=True, db_index=True, choices=COUNTRY_ISO.items())
    postal_code = models.CharField(max_length=30, blank=True, db_index=True)
    state = models.CharField(max_length=50, blank=True, db_index=True)
    city = models.CharField(max_length=100, blank=True, db_index=True)

    class Meta:
        abstract = True

    @property
    def is_named_location(self):
        return self.country != '' and self.state != '' and self.city != ''


class LocationMixin(AbstractLocationMixin, NamedLocationMixin):
    class Meta:
        abstract = True

    @property
    def location(self):
        return {
            'latitude': self.latitude,
            'longitude': self.longitude,
            'country': self.country,
            'postal_code': self.postal_code,
            'state': self.state,
            'city': self.city,
            'address': self.address,
        }

    @property
    def is_full_location(self):
        return not self.is_zero_coord and self.is_named_location


class CountryField(models.CharField):
    description = "2 Characters of a country ISO representation"

    def __init__(self, *args, **kwargs):
        kwargs['max_length'] = 2
        kwargs['blank'] = kwargs.get('blank', True)
        kwargs['db_index'] = kwargs.get('db_index', True)
        kwargs['choices'] = COUNTRY_CHOICES
        super(CountryField, self).__init__(*args, **kwargs)


class CountriesField(ArrayField):
    description = "List of country ISO representations"

    def __init__(self, *args, **kwargs):
        kwargs['base_field'] = CountryField()
        kwargs['blank'] = kwargs.get('blank', True)
        kwargs['default'] = kwargs.get('default', list)
        super(CountriesField, self).__init__(*args, **kwargs)
