from __future__ import unicode_literals

from django.apps import apps
from django.conf import settings
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver

from common.constants import ListenType, LISTEN_TYPE_PROFILE, LISTEN_TYPE_PAGE, LISTEN_TYPE_TAG
from .action import Action
from ..utils import track

AUTH_USER_MODEL = getattr(settings, 'AUTH_USER_MODEL')


class Listen2(Action):
    type = models.SmallIntegerField(choices=ListenType.choices)
    target = models.CharField(db_index=True, max_length=36)

    class Meta:
        unique_together = ('user', 'type', 'target')

    def __init__(self, *args, **kwargs):
        super(Action, self).__init__(*args, **kwargs)
        self._meta.get_field('user').blank = False

    def __unicode__(self):
        return "User: %s to %s: %s" % (self.user_id, self.get_type_display(), self.target)

    @classmethod
    def listen_type_and_target_from_object(cls, obj):
        if obj.model_name == 'User':
            obj = obj.ap
        listen_type = ListenType.texts[obj.model_name]
        return listen_type, getattr(obj, Listen2.target_attr(listen_type))

    @classmethod
    def target_attr(cls, listen_type):
        return {
            LISTEN_TYPE_PROFILE: 'pk',
            LISTEN_TYPE_PAGE: 'pk',
            LISTEN_TYPE_TAG: 'name',
        }[listen_type]

    @property
    def target_object(self):
        model = apps.get_model("shoutit", self.get_type_display())
        return model.objects.get(**{Listen2.target_attr(self.type): self.target})

    @property
    def track_properties(self):
        properties = {
            'type': self.get_type_display(),
            'target': self.target
        }
        return properties


@receiver(post_save, sender=Listen2)
def post_save_listen(sender, instance=None, created=False, **kwargs):
    if created:
        track(instance.user.pk, 'new_listen', instance.track_properties)
