"""

"""
from __future__ import unicode_literals
from django.conf import settings
from django.db import models
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from shoutit.models.base import UUIDModel, APIModelMixin, LocationMixin
from shoutit.utils import debug_logger

AUTH_USER_MODEL = getattr(settings, 'AUTH_USER_MODEL')


class Action(UUIDModel, APIModelMixin, LocationMixin):
    user = models.ForeignKey(AUTH_USER_MODEL, related_name='%(class)ss', null=True, blank=True)
    page_admin_user = models.ForeignKey(AUTH_USER_MODEL, related_name='pages_%(class)ss', null=True, blank=True)

    class Meta(UUIDModel.Meta):
        abstract = True

    @property
    def owner(self):
        return self.user


@receiver(pre_save)
def action_pre_save(sender, instance=None, created=False, **kwargs):
    if not issubclass(sender, Action):
        return
    ap = instance.user and instance.user.ap
    location = ap and ap.is_full_location and ap.location
    if instance.is_zero_coord and location:
        from shoutit.controllers import location_controller
        location_controller.update_object_location(instance, location, save=False)


@receiver(post_save)
def action_post_save(sender, instance=None, created=False, **kwargs):
    if not issubclass(sender, Action):
        return
    action = 'Created' if created else 'Updated'
    debug_logger.debug('%s %s: %s' % (action, instance.model_name, instance))
