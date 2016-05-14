from __future__ import unicode_literals

from django.conf import settings
from django.db import models
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from common.constants import USER_TYPE_PROFILE, TOKEN_TYPE_EMAIL
from shoutit.models.auth import AbstractProfile
from shoutit.models.misc import ConfirmToken
from shoutit.utils import correct_mobile, none_to_blank


AUTH_USER_MODEL = getattr(settings, 'AUTH_USER_MODEL')
gender_choices = [
    ('male', "Male"),
    ('female', "Male"),
]


class Profile(AbstractProfile):
    gender = models.CharField(max_length=10, blank=True, default='', choices=gender_choices)
    birthday = models.DateField(null=True, blank=True)
    bio = models.TextField(blank=True, max_length=512, default='')
    mobile = models.CharField(blank=True, max_length=20, default='')

    def __init__(self, *args, **kwargs):
        super(Profile, self).__init__(*args, **kwargs)

    def __unicode__(self):
        return unicode(self.user)

    def update(self, gender=None, birthday=None, bio=None, mobile=None):
        update_fields = []
        if gender:
            self.gender = gender
            update_fields.append('gender')
        if birthday:
            self.birthday = birthday
            update_fields.append('birthday')
        if bio:
            self.birthday = bio
            update_fields.append('bio')
        if mobile:
            self.mobile = mobile
            update_fields.append('mobile')
        self.save(update_fields=update_fields)

    def clean(self):
        super(Profile, self).clean()
        if self.mobile:
            self.mobile = correct_mobile(self.mobile, self.country)
        none_to_blank(self, ['gender', 'bio', 'mobile'])


@receiver(post_save, sender='shoutit.Profile')
def profile_post_save(sender, instance=None, created=False, **kwargs):
    pass


@receiver(pre_save, sender=AUTH_USER_MODEL)
def user_pre_save(sender, instance=None, created=False, update_fields=None, **kwargs):
    """

    """
    if instance.type != USER_TYPE_PROFILE:
        return
    if created:
        return
    if isinstance(update_fields, frozenset):
        if 'email' in update_fields:
            instance.take_activate_permission()
            instance.is_activated = False
        elif 'is_activated' in update_fields:
            if instance.is_activated:
                instance.give_activate_permission()
            else:
                instance.take_activate_permission()


@receiver(post_save, sender=AUTH_USER_MODEL)
def user_post_save(sender, instance=None, created=False, update_fields=None, **kwargs):
    """

    """
    if instance.type != USER_TYPE_PROFILE:
        return

    if created:
        # create profile
        profile_fields = getattr(instance, 'profile_fields', {})
        Profile.create(id=instance.id, user=instance, **profile_fields)

        # todo: give appropriate permissions
        # permissions = FULL_USER_PERMISSIONS if instance.is_activated else INITIAL_USER_PERMISSIONS
        # give_user_permissions(user=instance, permissions=permissions)

        # send signup email
        if not (instance.is_activated or instance.is_test):
            # create email confirmation token and send verification email
            ConfirmToken.create(user=instance, type=TOKEN_TYPE_EMAIL)
        if not instance.is_test and instance.email and '@sale.craigslist.org' not in instance.email:
            # Send welcome email
            instance.send_welcome_email()
            # Subscribe to mailing list
            instance.subscribe_to_mailing_list()
    else:
        if isinstance(update_fields, frozenset):
            if 'is_activated' in update_fields and instance.is_activated:
                instance.send_verified_email()
            elif 'email' in update_fields:
                instance.send_verification_email()
