"""

"""
from __future__ import unicode_literals

from django.db import models

from shoutit.models import User, Shout
from ..models import CreditRule, CREDIT_RULES, PromoteLabel


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
    Transactions of this rule must have: `shout_id`, `label_id` and `days`
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
        shout_id = transaction.properties.get('shout_id')
        if shout_id:
            shout = Shout.objects.get(id=shout_id)
            title = shout.title or 'shout'
            setattr(transaction, 'target', shout)
        else:
            title = 'shout'

        label_id = transaction.properties.get('label_id')
        if label_id:
            label = PromoteLabel.objects.get(id=label_id)
            label_name = label.name
        else:
            label_name = 'shout'

        days = transaction.properties.get('days')
        if days:
            text = self.text % (transaction.amount, title, label_name, days)
        else:
            text = self.text_no_days % (transaction.amount, title, label_name)
        ret = {
            "text": text,
            "ranges": [
                {'offset': text.index(title), 'length': len(title)},
                {'offset': text.index(label_name), 'length': len(label_name)}
            ]
        }
        return ret


CREDIT_RULES['promote_shouts'] = PromoteShouts
