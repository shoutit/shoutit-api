"""

"""
from __future__ import unicode_literals

from datetime import timedelta
from django.conf import settings
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django_pgjson.fields import JsonField

from common.constants import Constant
from common.utils import date_unix
from shoutit.models import UUIDModel

CREDIT_RULES = {}


class CreditTransactionType(Constant):
    counter, values, texts, choices = 0, {}, {}, ()


CREDIT_IN = CreditTransactionType('in')
CREDIT_OUT = CreditTransactionType('out')


class CreditRule(UUIDModel):
    transaction_type = models.SmallIntegerField(choices=CreditTransactionType.choices)
    type = models.CharField(max_length=30)
    name = models.CharField(max_length=50)
    description = models.CharField(max_length=250)
    options = JsonField(default=dict, blank=True)
    is_active = models.BooleanField(default=True)

    def __init__(self, *args, **kwargs):
        super(CreditRule, self).__init__(*args, **kwargs)
        if self.type:
            self.__class__ = CREDIT_RULES.get(self.type, CreditRule)

    def __unicode__(self):
        return "%s:%s:%s" % (self.get_transaction_type_display(), self.type, self.name)

    def display(self, transaction):
        raise NotImplementedError()


class CreditTransaction(UUIDModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='credit_transactions')
    amount = models.IntegerField()
    rule = models.ForeignKey(CreditRule, related_name='transactions')
    properties = JsonField(default=dict, blank=True)

    def __unicode__(self):
        return "%d:%s by %s" % (self.amount, self.rule, self.user)

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


@receiver(post_save, sender=CreditTransaction)
def user_post_save(sender, instance=None, created=False, update_fields=None, **kwargs):
    if created and getattr(instance, 'notify', True):
        instance.notify_user()


class PromoteLabel(UUIDModel):
    name = models.CharField(max_length=50)
    description = models.CharField(max_length=250)
    color = models.CharField(max_length=9)
    bg_color = models.CharField(max_length=9)
    rank = models.PositiveSmallIntegerField()

    def __unicode__(self):
        return "%s:%s" % (self.name, self.color)

    def clean(self):
        if not self.color.find('#'):
            self.color = '#' + self.color
        self.color = self.color.upper()

        if not self.bg_color.find('#'):
            self.bg_color = '#' + self.bg_color
        self.bg_color = self.bg_color.upper()


class ShoutPromotion(UUIDModel):
    shout = models.ForeignKey('shoutit.Shout', related_name='promotions')
    transaction = models.OneToOneField(CreditTransaction, related_name='shout_promotion')
    option = models.ForeignKey(CreditRule)
    label = models.ForeignKey(PromoteLabel)
    days = models.PositiveSmallIntegerField(blank=True, null=True, db_index=True)

    @property
    def expires_at(self):
        return self.created_at + timedelta(days=self.days)

    @property
    def expires_at_unix(self):
        return date_unix(self.expires_at)
