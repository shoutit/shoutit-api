"""

"""
from __future__ import unicode_literals

from django.conf import settings
from django.db import models
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver

from ..utils import debug_logger
from .base import UUIDModel, APIModelMixin, LocationMixin

AUTH_USER_MODEL = getattr(settings, 'AUTH_USER_MODEL')


class Action(UUIDModel, APIModelMixin, LocationMixin):
    user = models.ForeignKey(AUTH_USER_MODEL, related_name='%(class)ss', null=True, blank=True)
    page_admin_user = models.ForeignKey(AUTH_USER_MODEL, related_name='pages_%(class)ss', null=True, blank=True)

    class Meta(UUIDModel.Meta):
        abstract = True

    def __unicode__(self):
        return "%s" % self.pk

    @property
    def owner(self):
        return self.user

    def is_owner(self, user):
        return user == self.user or user == self.page_admin_user

    @property
    def track_properties(self):
        properties = {
            'id': self.pk,
            'profile': self.user_id,
            'mp_country_code': self.country,
            '$region': self.state,
            '$city': self.city,
            'api_client': getattr(self, 'api_client', None),
            'api_version': getattr(self, 'api_version', None),
        }
        if hasattr(self, 'get_type_display'):
            properties['type'] = self.get_type_display()

        return properties


@receiver(pre_save)
def action_pre_save(sender, instance=None, **kwargs):
    if not issubclass(sender, Action):
        return
    if instance.is_zero_coord:
        ap = instance.user and instance.user.ap
        location = ap and ap.is_full_location and ap.location
        if location:
            from shoutit.controllers import location_controller
            location_controller.update_object_location(instance, location, save=False)


@receiver(post_save)
def action_post_save(sender, instance=None, created=False, **kwargs):
    if not issubclass(sender, Action):
        return
    action = 'Created' if created else 'Updated'
    debug_logger.debug('%s %s: %s' % (action, instance.model_name, instance))
