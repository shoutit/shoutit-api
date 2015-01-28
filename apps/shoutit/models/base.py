import re
from datetime import datetime
from django.contrib.contenttypes.generic import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core import validators
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, UserManager
from django.core.mail import send_mail
from django.utils import timezone
from django.utils.http import urlquote
from django.utils.translation import ugettext_lazy as _
from push_notifications.models import APNSDevice, GCMDevice
from uuidfield import UUIDField


class UUIDModel(models.Model):
    id = UUIDField(auto=True, hyphenate=True, version=4, primary_key=True)
    created_at = models.DateTimeField(verbose_name=_("Creation time"), auto_now_add=True, null=True)
    modified_at = models.DateTimeField(verbose_name=_("Modification time"), auto_now=True, null=True)

    class Meta:
        abstract = True
        app_label = 'shoutit'

    @property
    def pk(self):
        return str(self.id).lower()

    @property
    def created_at_unix(self):
        return int((self.created_at - datetime(1970, 1, 1)).total_seconds())

    @property
    def modified_at_unix(self):
        return int((self.modified_at - datetime(1970, 1, 1)).total_seconds())


class AttachedObjectMixinManager(models.Manager):
    def with_attached_object(self, attached_object):
        ct = ContentType.objects.get_for_model(attached_object)
        return super(AttachedObjectMixinManager, self).get_query_set().filter(content_type=ct, object_id=attached_object.id)


class AttachedObjectMixin(models.Model):
    content_type = models.ForeignKey(ContentType, null=True)
    object_id = UUIDField(hyphenate=True, version=4, null=True)
    attached_object = GenericForeignKey('content_type', 'object_id')

    objects = AttachedObjectMixinManager()

    class Meta:
        abstract = True


class User(AbstractBaseUser, PermissionsMixin, UUIDModel):
    """
    An abstract base class implementing a fully featured User model with
    admin-compliant permissions and uuid field.

    Username, password and email are required. Other fields are optional.
    """
    username = models.CharField(_('username'), max_length=30, unique=True,
                                help_text=_('Required. 30 characters or fewer. Letters, numbers and . / _ characters'),
                                validators=[
                                    validators.RegexValidator(re.compile('^[\w.]+$'), _('Enter a valid username.'), 'invalid'),
                                ])
    first_name = models.CharField(_('first name'), max_length=30, blank=True)
    last_name = models.CharField(_('last name'), max_length=30, blank=True)
    email = models.EmailField(_('email address'), max_length=254, blank=True)
    is_staff = models.BooleanField(_('staff status'), default=False,
                                   help_text=_('Designates whether the user can log into this admin site.'))
    is_active = models.BooleanField(_('active'), default=True,
                                    help_text=_('Designates whether this user should be treated as '
                                                'active. Unselect this instead of deleting accounts.'))
    date_joined = models.DateTimeField(_('date joined'), default=timezone.now)

    objects = UserManager()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']

    class Meta(UUIDModel.Meta):
        verbose_name = _('user')
        verbose_name_plural = _('users')

    @property
    def abstract_profile(self):
        if hasattr(self, 'profile'):
            return self.profile
        elif hasattr(self, 'business'):
            return self.business
        else:
            return None

    @property
    def name(self):
        if hasattr(self, 'profile'):
            return self.get_full_name()
        elif hasattr(self, 'business'):
            return self.Business.Name
        else:
            return None

    # def request_count(self):
    # return Request.objects.filter(user__pk=self.pk).count()

    @property
    def apns_device(self):
        if hasattr(self, '_apns_device') and self._apns_device:
            return self._apns_device

        try:
            self._apns_device = APNSDevice.objects.get(user=self)
        except APNSDevice.DoesNotExist:
            self._apns_device = None

        return self._apns_device

    @property
    def gcm_device(self):
        if hasattr(self, '_gcm_device') and self._gcm_device:
            return self._gcm_device

        try:
            self._gcm_device = GCMDevice.objects.get(user=self)
        except GCMDevice.DoesNotExist:
            self._gcm_device = None

        return self._gcm_device

    def get_absolute_url(self):
        return "/users/%s/" % urlquote(self.username)

    def get_full_name(self):
        """
        Returns the first_name plus the last_name, with a space in between.
        """
        full_name = '%s %s' % (self.first_name, self.last_name)
        return full_name.strip()

    def get_short_name(self):
        "Returns the short name for the user."
        return self.first_name

    def email_user(self, subject, message, from_email=None):
        """
        Sends an email to this User.
        """
        send_mail(subject, message, from_email, [self.email])
