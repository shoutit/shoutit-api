"""

"""
from __future__ import unicode_literals

from django.db import models

from shoutit.api.v3.exceptions import ShoutitBadRequest
from shoutit.models import Shout
from ..models import CreditRule, CREDIT_RULES, PromoteLabel, CreditTransaction, ShoutPromotion


class ShareShouts(CreditRule):
    """
    Transactions of this rule must have: `shout_id`
    """
    text = "You earned 1 credit for sharing %s on Facebook."

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


CREDIT_RULES['share_shouts'] = ShareShouts


class PromoteShoutsManager(models.Manager):
    def get_queryset(self):
        return super(PromoteShoutsManager, self).get_queryset().filter(type='promote_shouts')


class PromoteShouts(CreditRule):
    """
    Transactions of this rule must have: `shout_promotion`
    """
    text = "You spent %d credits in promoting %s as '%s' shout for %d days."
    text_no_days = "You spent %d credits in promoting %s as '%s' shout."

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
        shout_title = shout.title
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
        transaction = CreditTransaction.create(user=user, amount=-self.credits, rule=self)

        # Create ShoutPromotion
        shout_promotion = ShoutPromotion.create(shout=shout, transaction=transaction, option=self, label=self.label,
                                                days=self.days)
        return shout_promotion

    def can_promote(self, shout, user):
        if user.stats.get('credit', 0) < self.credits:
            raise ShoutitBadRequest("You don't have enough Shoutit Credit for this action")

        if shout.promotions.exists():
            raise ShoutitBadRequest('This Shout is already promoted')


CREDIT_RULES['promote_shouts'] = PromoteShouts
