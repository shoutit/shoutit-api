from __future__ import unicode_literals
import re
import uuid
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core import validators
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, UserManager
from django.core.mail import send_mail
from django.utils import timezone
from django.utils.http import urlquote
from django.utils.translation import ugettext_lazy as _
from push_notifications.models import APNSDevice, GCMDevice
from common.utils import date_unix, AllowedUsernamesValidator
from shoutit.controllers import email_controller


class UUIDModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(verbose_name=_("Creation time"), auto_now_add=True, null=True)
    modified_at = models.DateTimeField(verbose_name=_("Modification time"), auto_now=True,
                                       null=True)

    class Meta:
        abstract = True

    def save(self, force_insert=False, force_update=False, **kwargs):
        if not (force_insert or force_update):
            self.full_clean()
        super(UUIDModel, self).save(force_insert, force_update, **kwargs)

    @property
    def pk(self):
        return str(self.id).lower()

    @property
    def created_at_unix(self):
        return date_unix(self.created_at)

    @property
    def modified_at_unix(self):
        return date_unix(self.modified_at)


class AttachedObjectMixinManager(models.Manager):
    def with_attached_object(self, attached_object):
        ct = ContentType.objects.get_for_model(attached_object)
        return super(AttachedObjectMixinManager, self).get_queryset().filter(content_type=ct,
                                                                             object_id=attached_object.id)


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
        return ''


class LocationMixin(models.Model):
    latitude = models.FloatField(
        validators=[validators.MaxValueValidator(90), validators.MinValueValidator(-90)])
    longitude = models.FloatField(
        validators=[validators.MaxValueValidator(180), validators.MinValueValidator(-180)])

    class Meta:
        abstract = True


class User(AbstractBaseUser, PermissionsMixin, UUIDModel, APIModelMixin):
    """
    An abstract base class implementing a fully featured User model with
    admin-compliant permissions and uuid field.

    Username, password and email are required. Other fields are optional.
    """
    username = models.CharField(_('username'), max_length=30, unique=True,
                                help_text=_(
                                    'Required. 2 to 30 characters and can only contain A-Z, a-z, 0-9, and periods (.)'),
                                validators=[
                                    validators.RegexValidator(re.compile('[0-9a-zA-Z.]{2,30}'),
                                                              _('Enter a valid username.'),
                                                              'invalid'),
                                    validators.MinLengthValidator(2),
                                    AllowedUsernamesValidator()
                                ])
    first_name = models.CharField(_('first name'), max_length=30, blank=True,
                                  validators=[validators.MinLengthValidator(2)])
    last_name = models.CharField(_('last name'), max_length=30, blank=True,
                                 validators=[validators.MinLengthValidator(1)])
    email = models.EmailField(_('email address'), blank=True)
    is_staff = models.BooleanField(_('staff status'), default=False,
                                   help_text=_(
                                       'Designates whether the user can log into this admin site.'))
    is_active = models.BooleanField(_('active'), default=True,
                                    help_text=_('Designates whether this user should be treated as '
                                                'active. Unselect this instead of deleting accounts.'))
    is_activated = models.BooleanField(_('activated'), default=False,
                                       help_text=_(
                                           'Designates whether this user have a verified email.'))
    date_joined = models.DateTimeField(_('date joined'), default=timezone.now)

    permissions = models.ManyToManyField('shoutit.Permission', through='shoutit.UserPermission')

    objects = UserManager()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']

    class Meta(UUIDModel.Meta):
        verbose_name = _('user')
        verbose_name_plural = _('users')

    def __unicode__(self):
        return "{} [{}:{}]".format(self.name, self.username, self.pk)

    @property
    def owner(self):
        return self

    @property
    def latitude(self):
        return self.profile.latitude

    @property
    def longitude(self):
        return self.profile.longitude

    @property
    def city(self):
        return self.profile.city

    @property
    def country(self):
        return self.profile.country

    @property
    def location(self):
        return {
            'country': self.country,
            'city': self.city,
            'latitude': self.latitude,
            'longitude': self.longitude,
        }

    @property
    def name(self):
        return self.get_full_name()

    @property
    def apns_device(self):
        if hasattr(self, '_apns_device'):
            return self._apns_device
        try:
            self._apns_device = APNSDevice.objects.get(user=self)
            return self._apns_device
        except APNSDevice.DoesNotExist:
            return None

    def delete_apns_device(self):
        if self.apns_device:
            self.apns_device.delete()
            if hasattr(self, '_apns_device'):
                delattr(self, '_apns_device')

    @property
    def gcm_device(self):
        if hasattr(self, '_gcm_device'):
            return self._gcm_device
        try:
            self._gcm_device = GCMDevice.objects.get(user=self)
            return self._gcm_device
        except GCMDevice.DoesNotExist:
            return None

    def delete_gcm_device(self):
        if self.gcm_device:
            self.gcm_device.delete()
            if hasattr(self, '_gcm_device'):
                delattr(self, '_gcm_device')

    @property
    def linked_accounts(self):
        if not hasattr(self, '_linked_accounts'):
            self._linked_accounts = {
                'facebook': True if (
                hasattr(self, 'linked_facebook') and self.linked_facebook) else False,
                'gplus': True if (hasattr(self, 'linked_gplus') and self.linked_gplus) else False,
            }
        return self._linked_accounts

    @property
    def push_tokens(self):
        if not hasattr(self, '_push_tokens'):
            self._push_tokens = {
                'apns': self.apns_device.registration_id if self.apns_device else None,
                'gcm': self.gcm_device.registration_id if self.gcm_device else None
            }
        return self._push_tokens

    def get_absolute_url(self):
        return "/users/%s/" % urlquote(self.username)

    def get_full_name(self):
        """
        Returns the first_name plus the last_name, with a space in between.
        username in case the above is empty string
        """
        full_name = '%s %s' % (self.first_name, self.last_name)
        full_name = full_name.strip()
        return full_name or self.username

    def get_short_name(self):
        "Returns the short name for the user."
        return self.first_name

    def email_user(self, subject, message, from_email=None):
        """
        Sends an email to this User.
        """
        send_mail(subject, message, from_email, [self.email])

    def activate(self):
        if self.is_activated:
            return
        from shoutit.permissions import give_user_permissions, ACTIVATED_USER_PERMISSIONS

        self.is_activated = True
        self.save(update_fields=['is_activated'])
        give_user_permissions(self, ACTIVATED_USER_PERMISSIONS)

    def send_verification_email(self):
        email_controller.send_signup_email(self)

    def send_signup_email(self):
        email_controller.send_signup_email(self)

    def send_reset_password_email(self):
        # todo: send using Mandrill SMTP
        pass

    def clean(self):
        self.email = self.email.lower()

    @property
    def is_password_set(self):
        return self.has_usable_password()
