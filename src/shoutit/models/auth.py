from __future__ import unicode_literals

import re
import sys
from collections import OrderedDict

from django.conf import settings
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, UserManager, AnonymousUser
from django.contrib.postgres.fields import ArrayField
from django.core import validators
from django.core.mail import send_mail
from django.db import models
from django.db.models import Q, Sum
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.utils import timezone, six
from django.utils.http import urlquote
from django.utils.translation import ugettext_lazy as _
from push_notifications.models import APNSDevice, GCMDevice
from pydash import arrays

from common.constants import (TOKEN_TYPE_RESET_PASSWORD, TOKEN_TYPE_EMAIL, USER_TYPE_PROFILE, UserType,
                              LISTEN_TYPE_PROFILE, LISTEN_TYPE_PAGE, LISTEN_TYPE_TAG)
from common.utils import AllowedUsernamesValidator, date_unix
from shoutit.utils import debug_logger, none_to_blank
from .base import UUIDModel, APIModelMixin, LocationMixin
from .listen import Listen2


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
        # used to later track signup events
        user.new_signup = True
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

    permissions = models.ManyToManyField(Permission, blank=True, through=UserPermission)
    type = models.PositiveSmallIntegerField(choices=UserType.choices, default=USER_TYPE_PROFILE.value, db_index=True)
    is_test = models.BooleanField(
        _('testuser status'), default=False, help_text=_('Designates whether this user is a test user.'))
    is_guest = models.BooleanField(
        _('guest user status'), default=False, help_text=_('Designates whether this user is a guest user.'))
    on_mailing_list = models.BooleanField(
        _('mailing list status'), default=False, help_text=_('Designates whether this user is on the main mailing list.'))
    on_mp_people = models.BooleanField(
        _('mixpanel people status'), default=False, help_text=_('Designates whether this user is on MixPanel People.'))
    objects = ShoutitUserManager()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']

    class Meta(UUIDModel.Meta):
        verbose_name = _('user')
        verbose_name_plural = _('users')

    def __unicode__(self):
        return "{} [{}:{}]".format(self.name if not self.is_guest else 'Guest', self.pk, self.username)

    def clean(self):
        self.email = self.email.lower()
        if self.is_test:
            self.is_activated = True

    @property
    def v3_type_name(self):
        return "user" if self.type == USER_TYPE_PROFILE else "page"

    @property
    def ap(self):
        return getattr(self, UserType.values[self.type].lower(), None)

    @property
    def name_username(self):
        return "{} [{}]".format(self.name if not self.is_guest else 'Guest', self.username)

    @property
    def owner(self):
        return self

    @property
    def location(self):
        return self.ap.location

    @property
    def name(self):
        if self.type == USER_TYPE_PROFILE:
            return self.get_full_name()
        elif hasattr(self, 'page'):
            return self.page.name
        else:
            return self.v3_type_name.capitalize()

    @property
    def apns_device(self):
        return APNSDevice.objects.filter(user=self).first()

    @property
    def has_apns(self):
        return self.apns_device is not None

    def send_apns(self, alert, **kwargs):
        from push_notifications.apns import apns_send_bulk_message
        if not self.has_apns:
            return
        apns_send_bulk_message(registration_ids=[self.apns_device.registration_id], alert=alert, **kwargs)

    def delete_apns_devices(self):
        APNSDevice.objects.filter(user=self).delete()
        debug_logger.debug("Deleted APNSDevices for %s" % self)

    @property
    def gcm_device(self):
        return GCMDevice.objects.filter(user=self).first()

    @property
    def has_gcm(self):
        return self.gcm_device is not None

    def send_gcm(self, data, **kwargs):
        from push_notifications.gcm import gcm_send_bulk_message
        if not self.has_gcm:
            return
        gcm_send_bulk_message(registration_ids=[self.gcm_device.registration_id], data=data, **kwargs)

    def delete_gcm_devices(self):
        GCMDevice.objects.filter(user=self).delete()
        debug_logger.debug("Deleted GCMDevices for %s" % self)

    def update_push_tokens(self, push_tokens_data, api_version):
        if 'apns' in push_tokens_data:
            apns_token = push_tokens_data.get('apns')
            # Delete user devices
            self.delete_apns_devices()
            if apns_token is not None:
                # Delete devices with same apns_token
                APNSDevice.objects.filter(registration_id=apns_token).delete()
                # Create new device for user with apns_token
                apns_device = APNSDevice(registration_id=apns_token, user=self)
                apns_device.api_version = api_version
                apns_device.save()

        if 'gcm' in push_tokens_data:
            gcm_token = push_tokens_data.get('gcm')
            # Delete user devices
            self.delete_gcm_devices()
            if gcm_token is not None:
                # Delete devices with same gcm_token
                GCMDevice.objects.filter(registration_id=gcm_token).delete()
                # Create new gcm device for user with gcm_token
                gcm_device = GCMDevice(registration_id=gcm_token, user=self)
                gcm_device.api_version = api_version
                gcm_device.save()

    @property
    def linked_accounts(self):
        linked_facebook = getattr(self, 'linked_facebook', None)
        linked_gplus = getattr(self, 'linked_gplus', None)
        _linked_accounts = {
            'gplus': {
                'gplus_id': linked_gplus.gplus_id
            } if linked_gplus else None,
            'facebook': OrderedDict([
                ('facebook_id', linked_facebook.facebook_id),
                ('expires_at', linked_facebook.expires_at_unix),
                ('scopes', linked_facebook.scopes)
            ]) if linked_facebook else None,
        }
        return _linked_accounts

    @property
    def v2_linked_accounts(self):
        linked_facebook = getattr(self, 'linked_facebook', None)
        has_linked_gplus = hasattr(self, 'linked_gplus')
        _linked_accounts = {
            'facebook': linked_facebook is not None,
            'gplus': has_linked_gplus,
        }
        if linked_facebook:
            _linked_accounts['facebook_details'] = {
                'facebook_id': linked_facebook.facebook_id,
                'access_token': linked_facebook.access_token,
                'expires_at': date_unix(linked_facebook.expires_at),
                'scopes': linked_facebook.scopes
            }
        return _linked_accounts

    @property
    def push_tokens(self):
        if not hasattr(self, '_push_tokens'):
            self._push_tokens = {
                'apns': self.apns_device.registration_id if self.apns_device else None,
                'gcm': self.gcm_device.registration_id if self.gcm_device else None
            }
        return self._push_tokens

    @property
    def api_client_names(self):
        return arrays.unique(self.accesstoken_set.values_list('client__name', flat=True))

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

    def mute_shouts(self):
        # Todo: optimize
        from shoutit.models import Shout
        for shout in Shout.objects.filter(user_id=self.id):
            shout.mute()

    def un_mute_shouts(self):
        # Todo: optimize
        from shoutit.models import Shout
        for shout in Shout.objects.filter(user_id=self.id):
            shout.unmute()

    def deactivate(self):
        self.is_activated = False
        self.save(update_fields=['is_activated'])

    def take_activate_permission(self):
        # from shoutit.permissions import take_permissions_from_user, ACTIVATED_USER_PERMISSIONS
        # take_permissions_from_user(self, ACTIVATED_USER_PERMISSIONS)
        pass

    def send_welcome_email(self):
        from ..controllers import email_controller
        email_controller.send_welcome_email(self)

    def subscribe_to_mailing_list(self):
        from ..controllers import email_controller
        email_controller.subscribe_users_to_mailing_list([self])

    def send_verified_email(self):
        from ..controllers import email_controller
        email_controller.send_verified_email(self)

    @property
    def verification_link(self):
        try:
            cf = self.confirmation_tokens.filter(type=TOKEN_TYPE_EMAIL, is_disabled=False)[0]
            return settings.SITE_LINK + 'auth/verify_email?token=' + cf.token
        except IndexError:
            return settings.SITE_LINK

    def send_verification_email(self):
        from .misc import ConfirmToken
        from ..controllers import email_controller
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
        from .misc import ConfirmToken
        from ..controllers import email_controller
        # invalidate other reset tokens
        self.confirmation_tokens.filter(type=TOKEN_TYPE_RESET_PASSWORD).update(is_disabled=True)
        # create new reset token
        ConfirmToken.objects.create(user=self, type=TOKEN_TYPE_RESET_PASSWORD)
        # email the user
        email_controller.send_password_reset_email(self)

    @property
    def is_password_set(self):
        return self.has_usable_password()

    @property
    def listening_count(self):
        return {
            'users': Listen2.objects.filter(user=self, type=LISTEN_TYPE_PROFILE).count(),
            'pages': Listen2.objects.filter(user=self, type=LISTEN_TYPE_PAGE).count(),
            'tags': Listen2.objects.filter(user=self, type=LISTEN_TYPE_TAG).count(),
        }

    def is_listening(self, obj):
        """
        Check whether the user of this profile is listening to this obj or not
        """
        listen_type, target = Listen2.listen_type_and_target_from_object(obj)
        return Listen2.exists(user=self, type=listen_type, target=target)

    @property
    def listening2_profile_ids(self):
        ids = Listen2.objects.filter(user=self).exclude(type=LISTEN_TYPE_TAG).values_list('target', flat=True)
        return list(ids)

    @property
    def listening2_profiles(self):
        return User.objects.filter(id__in=self.listening2_profile_ids)

    @property
    def listening2_users_ids(self):
        ids = Listen2.objects.filter(user=self, type=LISTEN_TYPE_PROFILE).values_list('target', flat=True)
        return list(ids)

    @property
    def listening2_users(self):
        from shoutit.models.user import Profile
        return Profile.objects.filter(id__in=self.listening2_users_ids)

    @property
    def listening2_pages_ids(self):
        ids = Listen2.objects.filter(user=self, type=LISTEN_TYPE_PAGE).values_list('target', flat=True)
        return list(ids)

    @property
    def listening2_pages(self):
        from shoutit.models.page import Page
        return Page.objects.filter(id__in=self.listening2_pages_ids)

    @property
    def listening2_tags_names(self):
        names = Listen2.objects.filter(user=self, type=LISTEN_TYPE_TAG).values_list('target', flat=True)
        return list(names)

    @property
    def listening2_tags(self):
        from shoutit.models.tag import Tag
        return Tag.objects.filter(name__in=self.listening2_tags_names)

    @property
    def listening2(self):
        return {
            'users': self.listening2_users,
            'pages': self.listening2_pages,
            'tags': self.listening2_tags,
        }

    @property
    def listeners_count(self):
        listen_type, target = Listen2.listen_type_and_target_from_object(self)
        return Listen2.objects.filter(type=listen_type, target=target).count()

    @property
    def stats(self):
        from ..controllers import notifications_controller
        # Todo (mo): crate fields for each stats property which holds the latest value and gets updated
        if not hasattr(self, '_stats'):
            unread_conversations_count = notifications_controller.get_unread_conversations_count(self)
            unread_notifications_count = notifications_controller.get_unread_actual_notifications_count(self)
            credit = self.credit_transactions.aggregate(sum=Sum('amount'))['sum'] or 0
            self._stats = OrderedDict([
                ('unread_conversations_count', unread_conversations_count),
                ('unread_notifications_count', unread_notifications_count),
                ('total_unread_count', unread_conversations_count + unread_notifications_count),
                ('credit', credit),
            ])
        return self._stats

    @property
    def mutual_friends(self):
        if not hasattr(self, 'linked_facebook'):
            return User.objects.none()
        friends = Q(linked_facebook__facebook_id__in=self.linked_facebook.friends)
        friend = Q(linked_facebook__friends__contains=[self.linked_facebook.facebook_id])
        return User.objects.filter(friends | friend).exclude(id=self.id)

    @property
    def mutual_contacts(self):
        from shoutit.models import Profile
        values = self.contacts.values_list('emails', 'mobiles')
        if not values:
            return User.objects.none()
        emails_list, mobiles_list = arrays.unzip(values)
        emails = filter(None, arrays.flatten(emails_list))
        mobiles = filter(None, arrays.flatten(mobiles_list))
        profile_ids = Profile.objects.filter(mobile__in=mobiles).values_list('id', flat=True)
        return User.objects.filter(Q(email__in=emails) | Q(id__in=profile_ids)).exclude(id=self.id)


@receiver(post_save, sender=User)
def user_post_save(sender, instance=None, created=False, update_fields=None, **kwargs):
    from shoutit.controllers import notifications_controller
    action = 'Created' if created else 'Updated'
    is_guest = 'Guest' if instance.is_guest else ''
    notify = getattr(instance, 'notify', True)
    debug_logger.debug('%s %sUser: %s | Notify: %s' % (action, is_guest, instance, notify))

    # Mute / unmute user shouts if his active state was changed
    if isinstance(update_fields, frozenset):
        if 'is_active' in update_fields:
            if instance.is_active:
                instance.un_mute_shouts()
            else:
                instance.mute_shouts()

    if not created:
        if notify:
            # Send notification about user changes
            notifications_controller.notify_user_of_profile_update(instance)


class InactiveUser(AnonymousUser):
    # Todo: add init function that accepts the actual inactive user
    @property
    def to_dict(self):
        return OrderedDict({
            "id": "",
            "api_url": "",
            "web_url": "",
            "username": "",
            "name": "Shoutit User",
            "is_activated": False,
            "image": "",
        })

# Todo: Add DeletedUser class


class AbstractProfile(UUIDModel, LocationMixin):
    user = models.OneToOneField(User, related_name='%(class)s')
    image = models.URLField(blank=True, default='')
    cover = models.URLField(blank=True, default='')
    video = models.OneToOneField('shoutit.Video', related_name='%(class)s', null=True, blank=True,
                                 on_delete=models.SET_NULL)
    website = models.URLField(blank=True, default='')

    class Meta(UUIDModel.Meta):
        abstract = True

    def __getattribute__(self, item):
        """
        If an attribute does not exist on this instance, then we also attempt to proxy it to the underlying User object.
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

    def clean(self):
        none_to_blank(self, ['image', 'cover', 'website'])


@receiver(post_save)
def abstract_profile_post_save(sender, instance=None, created=False, **kwargs):
    from shoutit.controllers import notifications_controller
    if not issubclass(sender, AbstractProfile):
        return
    action = 'Created' if created else 'Updated'
    notify = getattr(instance, 'notify', True)
    debug_logger.debug('%s %s: %s | Notify: %s' % (action, instance.model_name, instance, notify))

    if not created:
        if notify:
            # Send `profile_update` notification
            notifications_controller.notify_user_of_profile_update(instance.user)


class LinkedFacebookAccount(UUIDModel):
    user = models.OneToOneField(User, related_name='linked_facebook')
    facebook_id = models.CharField(max_length=24, unique=True)
    access_token = models.CharField(max_length=512)
    expires_at = models.DateTimeField()
    scopes = ArrayField(models.CharField(max_length=50), default=['public_profile', 'email'], blank=True)
    friends = ArrayField(models.CharField(max_length=24), default=list, blank=True)

    def __unicode__(self):
        return unicode(self.user)

    @property
    def expires_at_unix(self):
        return date_unix(self.expires_at)


@receiver(post_save, sender=LinkedFacebookAccount)
def linked_facebook_account_post_save(sender, instance, created, **kwargs):
    action = 'Created' if created else 'Updated'
    debug_logger.debug('%s LinkedFacebookAccount for %s' % (action, instance.user))


@receiver(post_delete, sender=LinkedFacebookAccount)
def linked_facebook_account_post_delete(sender, instance, **kwargs):
    debug_logger.debug('Deleted LinkedFacebookAccount for %s' % instance.user)


class LinkedGoogleAccount(UUIDModel):
    user = models.OneToOneField(User, related_name='linked_gplus')
    gplus_id = models.CharField(max_length=64, unique=True)
    credentials_json = models.CharField(max_length=4096)

    def __unicode__(self):
        return unicode(self.user)


class ProfileContact(UUIDModel):
    user = models.ForeignKey(User, related_name='contacts')
    first_name = models.CharField(_('first name'), max_length=30, blank=True)
    last_name = models.CharField(_('last name'), max_length=30, blank=True)
    emails = ArrayField(models.EmailField(_('email address'), blank=True), default=list, blank=True)
    mobiles = ArrayField(models.CharField(_('mobile'), max_length=20, blank=True), default=list, blank=True)

    def clean(self):
        self.emails = filter(None, self.emails)
        self.mobiles = filter(None, self.mobiles)

    def is_empty(self):
        return all([not self.first_name, not self.last_name, not self.emails, not self.mobiles])

    def is_reached(self):
        return any([self.emails, self.mobiles])
