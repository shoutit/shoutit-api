"""

"""
from __future__ import unicode_literals

from django.db import models

from shoutit.models import User, Shout
from ..models import CreditRule, CREDIT_RULES, PromoteLabel


class ShareShouts(CreditRule):
    text = "You earned 1 credit for sharing %s on Facebook."

    class Meta:
        proxy = True

    def display(self, transaction):
        shout_id = transaction.properties.get('shout_id')
        if shout_id:
            shout = Shout.objects.get(id=shout_id)
            title = shout.title
            setattr(transaction, 'target', shout)
        else:
            title = 'a shout'
        text = self.text % title
        ret = {
            "text": text,
            "ranges": [{'offset': text.index(title), 'length': len(title)}]
        }
        return ret


CREDIT_RULES['share_shouts'] = ShareShouts


class PromoteShoutsManager(models.Manager):
    def get_queryset(self):
        return super(PromoteShoutsManager, self).get_queryset().filter(type='promote_shouts')


class PromoteShouts(CreditRule):
    text = "You spent %s credit in promoting %s for %s."

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
        profile_id = transaction.properties.get('profile_id')
        if profile_id:
            profile = User.objects.get(id=profile_id)
            name = profile.name
            setattr(transaction, 'target', profile)
        else:
            name = 'a friend'
        text = self.text % name
        ret = {
            "text": text,
            "ranges": [{'offset': text.index(name), 'length': len(name)}]
        }
        return ret


CREDIT_RULES['promote_shouts'] = PromoteShouts
