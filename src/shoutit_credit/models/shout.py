"""

"""
from __future__ import unicode_literals

from datetime import timedelta

from django.conf import settings
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django_rq import job

from common.utils import date_unix
from shoutit.api.v3.exceptions import ShoutitBadRequest
from shoutit.models import UUIDModel, Shout
from .base import CreditRule, CreditTransaction

share_shouts = None


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
    shout = models.ForeignKey(Shout, related_name='promotions')
    label = models.ForeignKey(PromoteLabel)

    days = models.PositiveSmallIntegerField(blank=True, null=True, db_index=True)
    transaction = models.OneToOneField(CreditTransaction, blank=True, null=True, related_name='shout_promotion')
    option = models.ForeignKey('shoutit_credit.PromoteShouts', blank=True, null=True)

    @property
    def expires_at(self):
        return self.created_at + timedelta(days=self.days) if self.days else None

    @property
    def expires_at_unix(self):
        return date_unix(self.expires_at) if self.days else None


class ShareShoutsManager(models.Manager):
    def get_queryset(self):
        return super(ShareShoutsManager, self).get_queryset().filter(type='share_shouts')


class ShareShouts(CreditRule):
    """
    Transactions of this rule must have: `shout_id`
    """
    text = "You earned 1 Shoutit Credit for sharing %s on Facebook."

    objects = ShareShoutsManager()

    class Meta:
        proxy = True

    def display(self, transaction):
        if hasattr(self, '_display'):
            return self._display

        shout_id = transaction.properties.get('shout_id')
        if shout_id:
            shout = Shout.objects.get(id=shout_id)
            title = shout.title or 'shout'
            setattr(transaction, 'target', shout)
        else:
            title = 'shout'
        text = self.text % title
        ret = {
            "text": text,
            "ranges": [
                {'offset': text.index(title), 'length': len(title)}
            ]
        }

        setattr(self, '_display', ret)
        return self._display

    def apply(self, shout):
        shout_id = shout.pk
        user_id = shout.user_id

        # Check for similar existing transaction
        if CreditTransaction.exists(user_id=user_id, rule=self, properties__at_shout_id=shout_id):
            return

        # Create Credit Transaction
        properties = {'shout_id': shout_id}
        transaction = CreditTransaction.create(user_id=user_id, amount=1, rule=self, properties=properties)
        return transaction


@job(settings.RQ_QUEUE_CREDIT)
def apply_share_shouts(profile):
    global share_shouts
    if not share_shouts:
        share_shouts = ShareShouts.objects.first()
    if share_shouts:
        share_shouts.apply(profile)


@receiver(post_save, sender=Shout)
def shout_post_save(sender, instance=None, created=False, update_fields=None, **kwargs):
    if 'facebook' in instance.published_on:
        apply_share_shouts.delay(instance)


class PromoteShoutsManager(models.Manager):
    def get_queryset(self):
        return super(PromoteShoutsManager, self).get_queryset().filter(type='promote_shouts')


class PromoteShouts(CreditRule):
    """
    Transactions of this rule must have: `shout_promotion`
    """
    text = "You spent %d Shoutit Credit in promoting %s as %s for %d days."
    text_no_days = "You spent %d Shoutit Credit in promoting %s as '%s'."

    objects = PromoteShoutsManager()

    class Meta:
        proxy = True

    @property
    def label(self):
        label_id = self.options.get('label_id')
        return PromoteLabel.objects.filter(id=label_id).first() if label_id else None

    @property
    def credits(self):
        return self.options.get('credits')

    @property
    def days(self):
        return self.options.get('days')

    @property
    def rank(self):
        return self.options.get('rank')

    def display(self, transaction):
        shout_promotion = transaction.shout_promotion
        shout = shout_promotion.shout
        label = shout_promotion.label
        days = shout_promotion.days
        shout_title = shout.title or 'a shout'
        label_name = label.name

        if days:
            text = self.text % (abs(transaction.amount), shout_title, label_name, days)
        else:
            text = self.text_no_days % (abs(transaction.amount), shout_title, label_name)
        ret = {
            "text": text,
            "ranges": [
                {'offset': text.index(shout_title), 'length': len(shout_title)},
                {'offset': text.index(label_name), 'length': len(label_name)}
            ]
        }
        return ret

    def apply(self, shout, user):
        self.can_promote(shout, user)

        # Create Credit Transaction
        transaction = CreditTransaction.create(save=False, user=user, amount=-self.credits, rule=self)
        transaction.notify = False
        transaction.save()

        # Create ShoutPromotion
        shout_promotion = ShoutPromotion.create(shout=shout, label=self.label, days=self.days, transaction=transaction,
                                                option=self)

        # We need to save the promotion before notifying as the notification requires the promotion object
        transaction.notify_user()
        return shout_promotion

    def can_promote(self, shout, user):
        if user.stats.get('credit', 0) < self.credits:
            raise ShoutitBadRequest("You don't have enough Shoutit Credit for this action")

        if shout.promotions.exists():
            raise ShoutitBadRequest('This Shout is already promoted')
