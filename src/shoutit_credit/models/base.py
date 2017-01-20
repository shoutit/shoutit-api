"""

"""
from __future__ import unicode_literals

from django.conf import settings
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django_pgjson.fields import JsonField
from hvad.models import TranslatedFields, TranslatableModel

from common.constants import Constant
from shoutit.models import UUIDModel
from shoutit.models.base import TranslatedModelFallbackMixin

CREDIT_RULES = {}


class CreditTransactionType(Constant):
    counter, values, texts, choices = 0, {}, {}, ()


CREDIT_IN = CreditTransactionType('in')
CREDIT_OUT = CreditTransactionType('out')


class CreditRule(TranslatedModelFallbackMixin, TranslatableModel, UUIDModel):
    transaction_type = models.SmallIntegerField(choices=CreditTransactionType.choices)
    type = models.CharField(max_length=30)
    name = models.CharField(max_length=50)
    description = models.CharField(max_length=250, blank=True, default='')
    options = JsonField(default=dict, blank=True)
    is_active = models.BooleanField(default=True)

    translations = TranslatedFields(
        _local_name=models.CharField(max_length=50, blank=True, default=''),
        _local_description=models.CharField(max_length=250, blank=True, default='')
    )

    def __init__(self, *args, **kwargs):
        super(CreditRule, self).__init__(*args, **kwargs)
        if self.type:
            self.__class__ = CREDIT_RULES.get(self.type, CreditRule)

    def __str__(self):
        return "%s:%s:%s" % (self.get_transaction_type_display(), self.type, self.name)

    def display(self, transaction):
        raise NotImplementedError()


class CreditTransaction(UUIDModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='credit_transactions')
    amount = models.IntegerField()
    rule = models.ForeignKey(CreditRule, related_name='transactions')
    properties = JsonField(default=dict, blank=True)

    def __str__(self):
        return "%s %d:%s by %s" % (self.id, self.amount, self.rule, self.user.username)

    @property
    def type(self):
        return CREDIT_IN if self.amount > 0 else CREDIT_OUT

    def get_type_display(self):
        return str(self.type)

    def display(self):
        return self.rule.display(self)

    @property
    def app_url(self):
        self.display()
        return getattr(self.target, 'app_url', None) if hasattr(self, 'target') else None

    @property
    def web_url(self):
        self.display()
        return getattr(self.target, 'web_url', None) if hasattr(self, 'target') else None

    def notify_user(self):
        from shoutit.controllers.notifications_controller import notify_user_of_credit_transaction
        notify_user_of_credit_transaction(self)

    def serializer(self, version=None):
        from shoutit_credit.serializers import CreditTransactionSerializer
        return CreditTransactionSerializer


@receiver(post_save, sender=CreditTransaction)
def transaction_post_save(sender, instance=None, created=False, update_fields=None, **kwargs):
    if created and getattr(instance, 'notify', True):
        instance.notify_user()
