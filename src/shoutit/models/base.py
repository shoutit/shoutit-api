from __future__ import unicode_literals

import urlparse
import uuid
from urllib import urlencode

from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.contrib.postgres.fields import ArrayField
from django.core import validators
from django.db import models
from django.utils.translation import ugettext_lazy as _
from hvad.manager import TranslationManager
from mptt.managers import TreeManager

from common.constants import COUNTRY_ISO, COUNTRY_CHOICES
from common.utils import date_unix


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

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None, exclude=None,
             validate_unique=True):
        if not (force_insert or force_update):
            self.full_clean(exclude=exclude, validate_unique=validate_unique)
        super(UUIDModel, self).save(force_insert=force_insert, force_update=force_update, using=using,
                                    update_fields=update_fields)

    def update(self, **kwargs):
        field_names = self._meta.get_all_field_names()
        update_fields = []
        for k in kwargs.keys():
            if k in field_names:
                setattr(self, k, kwargs[k])
                update_fields.append(k)
        self.save(update_fields=update_fields)
        return self

    @classmethod
    def exists(cls, *args, **kwargs):
        return cls.objects.filter(*args, **kwargs).exists()

    @property
    def created_at_unix(self):
        return date_unix(self.created_at)

    @property
    def modified_at_unix(self):
        return date_unix(self.modified_at)

    @property
    def model_name(self):
        return type(self).__name__


class TranslationTreeManager(TranslationManager, TreeManager):
    use_for_related_fields = True


class TranslatedModelFallbackMixin(object):
    """
    This returns the shared field value of the Translated Model if the translated field value is empty.
    Subclasses must define translated fields named after the shared ones according to this example

    ```
    class Tag(TranslatableModel):
        name = CharField(max_length=30)  # Shared Field

        translations = TranslatedFields(
            _local_name=models.CharField(max_length=30)  # Translated Field
        )
    ```
    """
    def __getattribute__(self, item):
        if not item.startswith('_local_'):
            return super(TranslatedModelFallbackMixin, self).__getattribute__(item)

        translated_value = super(TranslatedModelFallbackMixin, self).__getattribute__(item)
        if item in self._translated_field_names and translated_value == '':
            shared_item = item.replace('_local_', '')
            return super(TranslatedModelFallbackMixin, self).__getattribute__(shared_item)

        return translated_value


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
            # class: ('netloc', 'identity_attr')
            'user': ('user', 'username'),
            'tag': ('tag', 'name'),
            'shout': ('shout', 'id'),
            'discoveritem': ('discover', 'id'),
            'conversation': ('messages', 'id'),
        }
        netloc, identity_attr = lookups.get(name, (name, 'id'))
        identity = getattr(self, identity_attr, '')
        return "%s%s/%s" % (settings.SITE_LINK, netloc, identity)

    @property
    def app_url(self):
        name = self.__class__.__name__.lower()
        lookups = {
            # class: ('netloc', 'attr_name')
            # attr_name can be string or (attr_name, param_name)
            'user': ('profile', 'username'),
            'shout': ('shout', 'id'),
            'message': ('conversation', ('conversation_id', 'id')),
            'conversation': ('conversation', 'id'),
            'discoveritem': ('discover', 'id'),
        }
        netloc, attr_name = lookups.get(name, (name, 'id'))
        if isinstance(attr_name, basestring):
            attr_name = (attr_name, attr_name)
        attr_value = getattr(self, attr_name[0], '')
        params = urlencode({attr_name[1]: attr_value})
        url = urlparse.urlunparse((settings.APP_LINK_SCHEMA, netloc, '', '', params, ''))
        return url


class AbstractLocationMixin(models.Model):
    latitude = models.FloatField(
        default=0, validators=[validators.MaxValueValidator(90), validators.MinValueValidator(-90)])
    longitude = models.FloatField(
        default=0, validators=[validators.MaxValueValidator(180), validators.MinValueValidator(-180)])
    address = models.CharField(max_length=200, blank=True)

    class Meta:
        abstract = True

    @property
    def location(self):
        return {
            'latitude': self.latitude,
            'longitude': self.longitude
        }

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
    def location(self):
        return {
            'country': self.country,
            'postal_code': self.postal_code,
            'state': self.state,
            'city': self.city
        }

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
            'address': self.address
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
