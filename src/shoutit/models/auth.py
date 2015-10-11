from __future__ import unicode_literals
import re

from django.conf import settings
from django.contrib.contenttypes.fields import GenericRelation
from django.core import validators
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, UserManager
from django.core.mail import send_mail
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone, six
from django.utils.http import urlquote
from django.utils.translation import ugettext_lazy as _
from push_notifications.models import APNSDevice, GCMDevice
import sys

from common.utils import AllowedUsernamesValidator
from common.constants import (TOKEN_TYPE_RESET_PASSWORD, TOKEN_TYPE_EMAIL, USER_TYPE_PROFILE, UserType,
                              Stream_TYPE_PROFILE, Stream_TYPE_TAG)
from shoutit.controllers import email_controller
from shoutit.models.base import UUIDModel, APIModelMixin, LocationMixin
from shoutit.models.stream import StreamMixin, Listen
from shoutit.utils import debug_logger


class ShoutitUserManager(UserManager):
    def _create_user(self, username, email, password, is_staff, is_superuser, **extra_fields):
        """
        Creates and saves a User with the given username, email and password.
        An extra profile_fields is to be passed so the user_post_save method can setup the
        Profile to prevent multiple saves / updates when creating new users.
        """
        now = timezone.now()
        if not username:
            raise ValueError('The given username must be set')
        email = self.normalize_email(email)
        profile_fields = extra_fields.pop('profile_fields', {})
        page_fields = extra_fields.pop('page_fields', {})
        user = self.model(username=username, email=email, is_staff=is_staff, is_active=True, is_superuser=is_superuser,
                          date_joined=now, **extra_fields)
        user.set_password(password)
        user.profile_fields = profile_fields
        user.page_fields = page_fields
        user.save(using=self._db)
        return user


class Permission(UUIDModel):
    name = models.CharField(max_length=512, unique=True, db_index=True)

    def __unicode__(self):
        return self.name


class UserPermission(UUIDModel):
    user = models.ForeignKey('User')
    permission = models.ForeignKey(Permission)
    date_given = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return '%s: %s' % (unicode(self.user), unicode(self.permission))


class User(AbstractBaseUser, PermissionsMixin, UUIDModel, APIModelMixin):
    """
    An abstract base class implementing a fully featured User model with
    admin-compliant permissions and uuid field.

    Username, password and email are required. Other fields are optional.
    """
    username = models.CharField(
        _('username'), max_length=30, unique=True, help_text=_(
            'Required. 2 to 30 characters and can only contain A-Z, a-z, 0-9, and periods (.)'),
        validators=[
            validators.RegexValidator(
                re.compile('^[0-9a-zA-Z.]+$'), _('Enter a valid username.'), 'invalid'),
            validators.MinLengthValidator(2),
            AllowedUsernamesValidator()
        ])
    first_name = models.CharField(
        _('first name'), max_length=30, blank=True, validators=[validators.MinLengthValidator(2)])
    last_name = models.CharField(
        _('last name'), max_length=30, blank=True, validators=[validators.MinLengthValidator(1)])
    email = models.EmailField(_('email address'), blank=True)
    is_staff = models.BooleanField(
        _('staff status'), default=False, help_text=_('Designates whether the user can log into this admin site.'))
    is_active = models.BooleanField(
        _('active'), default=True, help_text=_(
            'Designates whether this user should be treated as active. Unselect this instead of deleting accounts.'))
    is_activated = models.BooleanField(
        _('activated'), default=False, help_text=_('Designates whether this user have a verified email.'))
    date_joined = models.DateTimeField(_('date joined'), default=timezone.now)

    permissions = models.ManyToManyField(Permission, through=UserPermission)
    type = models.PositiveSmallIntegerField(choices=UserType.choices, default=USER_TYPE_PROFILE.value, db_index=True)
    is_test = models.BooleanField(
        _('testuser status'), default=False, help_text=_('Designates whether this user is a test user.'))
    objects = ShoutitUserManager()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']

    class Meta(UUIDModel.Meta):
        verbose_name = _('user')
        verbose_name_plural = _('users')

    def __unicode__(self):
        return "{} [{}:{}]".format(self.name, self.pk, self.username)

    @property
    def ap(self):
        return getattr(self, UserType.values[self.type].lower(), None)

    @property
    def name_username(self):
        return "{} [{}]".format(self.name, self.username)

    @property
    def owner(self):
        return self

    @property
    def location(self):
        return self.ap.location

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

    @property
    def api_client_name(self):
        if self.accesstoken_set.exists():
            return self.accesstoken_set.all()[0].client.name
        return 'none'

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
        """
        Returns the short name for the user.
        """
        return self.first_name

    def email_user(self, subject, message, from_email=None):
        """
        Sends an email to this User.
        """
        send_mail(subject, message, from_email, [self.email])

    def activate(self):
        self.is_activated = True
        self.save(update_fields=['is_activated'])

    def give_activate_permission(self):
        # from shoutit.permissions import give_user_permissions, ACTIVATED_USER_PERMISSIONS
        # give_user_permissions(self, ACTIVATED_USER_PERMISSIONS)
        pass

    def deactivate(self):
        self.is_activated = False
        self.save(update_fields=['is_activated'])

    def take_activate_permission(self):
        # from shoutit.permissions import take_permissions_from_user, ACTIVATED_USER_PERMISSIONS
        # take_permissions_from_user(self, ACTIVATED_USER_PERMISSIONS)
        pass

    def send_signup_email(self):
        email_controller.send_signup_email(self)

    def send_verified_email(self):
        email_controller.send_verified_email(self)

    @property
    def verification_link(self):
        try:
            cf = self.confirmation_tokens.filter(type=TOKEN_TYPE_EMAIL, is_disabled=False)[0]
            return settings.SITE_LINK + 'auth/verify_email?token=' + cf.token
        except IndexError:
            return settings.SITE_LINK

    def send_verification_email(self):
        from shoutit.models import ConfirmToken
        # invalidate other reset tokens
        self.confirmation_tokens.filter(type=TOKEN_TYPE_EMAIL).update(is_disabled=True)
        # create new reset token
        ConfirmToken.objects.create(user=self, type=TOKEN_TYPE_EMAIL)
        # email the user
        email_controller.send_verification_email(self)

    @property
    def password_reset_link(self):
        try:
            cf = self.confirmation_tokens.filter(type=TOKEN_TYPE_RESET_PASSWORD, is_disabled=False)[0]
            return settings.SITE_LINK + 'services/reset_password?reset_token=' + cf.token
        except IndexError:
            return settings.SITE_LINK

    def reset_password(self):
        from shoutit.models import ConfirmToken
        # invalidate other reset tokens
        self.confirmation_tokens.filter(type=TOKEN_TYPE_RESET_PASSWORD).update(is_disabled=True)
        # create new reset token
        ConfirmToken.objects.create(user=self, type=TOKEN_TYPE_RESET_PASSWORD)
        # email the user
        email_controller.send_password_reset_email(self)

    def clean(self):
        self.email = self.email.lower()

    @property
    def is_password_set(self):
        return self.has_usable_password()


@receiver(post_save, sender=User)
def user_post_save(sender, instance=None, created=False, update_fields=None, **kwargs):
    action = 'Created' if created else 'Updated'
    debug_logger.debug('%s User: %s' % (action, instance))


class AbstractProfile(UUIDModel, StreamMixin, LocationMixin):
    user = models.OneToOneField(User, related_name='%(class)s', db_index=True)
    _stream = GenericRelation('shoutit.Stream')
    # feed = models.ManyToManyField('shoutit.Post', through='shoutit.FeedPost')

    image = models.URLField(blank=True, default='')
    cover = models.URLField(blank=True, default='')
    video = models.OneToOneField('shoutit.Video', related_name='%(class)s', null=True, blank=True,
                                 on_delete=models.SET_NULL)
    website = models.URLField(blank=True, default='')

    class Meta(UUIDModel.Meta):
        abstract = True

    def __init__(self, *args, **kwargs):
        super(AbstractProfile, self).__init__(*args, **kwargs)

        # Setting related_query_name to %(class)s is not permitted as it is in related_name
        # https://code.djangoproject.com/ticket/25354
        self._meta.get_field('_stream').related_query_name = lambda: self._meta.model_name

    def __getattribute__(self, item):
        """
        If an attribute does not exist on this instance, then we also attempt to proxy it to the underlying
        User object.
        """
        try:
            return super(AbstractProfile, self).__getattribute__(item)
        except AttributeError:
            info = sys.exc_info()
            try:
                if item in ['user', '_user_cache']:
                    raise AttributeError
                return getattr(self.user, item)
            except AttributeError:
                six.reraise(info[0], info[1], info[2].tb_next)

    def is_listener(self, stream):
        """
        Check whether the user of this profile is listening to this stream or not
        """
        return Listen.objects.filter(listener=self.user, stream=stream).exists()

    @property
    def listening_count(self):
        return {
            'users': Listen.objects.filter(listener=self.user, stream__type=Stream_TYPE_PROFILE).count(),
            'tags': Listen.objects.filter(listener=self.user, stream__type=Stream_TYPE_TAG).count()
        }

    @property
    def owner(self):
        return self.user


@receiver(post_save)
def abstract_profile_post_save(sender, instance=None, created=False, **kwargs):
    if not issubclass(sender, AbstractProfile):
        return
    action = 'Created' if created else 'Updated'
    debug_logger.debug('%s %s: %s' % (action, instance.model_name, instance))


class LinkedFacebookAccount(UUIDModel):
    user = models.OneToOneField(User, related_name='linked_facebook', db_index=True)
    facebook_id = models.CharField(max_length=24, db_index=True, unique=True)
    access_token = models.CharField(max_length=512)
    expires = models.BigIntegerField(default=0)

    def __unicode__(self):
        return unicode(self.user)


class LinkedGoogleAccount(UUIDModel):
    user = models.OneToOneField(User, related_name='linked_gplus', db_index=True)
    gplus_id = models.CharField(max_length=64, db_index=True, unique=True)
    credentials_json = models.CharField(max_length=4096)

    def __unicode__(self):
        return unicode(self.user)
