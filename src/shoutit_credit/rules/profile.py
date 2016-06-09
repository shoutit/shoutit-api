"""

"""
from __future__ import unicode_literals

from shoutit.models import User
from ..models import CreditRule, CREDIT_RULES


class CompleteProfile(CreditRule):
    text = "You earned 1 credit for completing your profile."

    class Meta:
        proxy = True

    def display(self, transaction):
        setattr(transaction, 'target', transaction.user)
        ret = {
            "text": self.text,
            "ranges": []
        }
        return ret


CREDIT_RULES['cp'] = CompleteProfile


class InviteFriend(CreditRule):
    text = "You earned 1 credit for inviting %s."

    class Meta:
        proxy = True

    def display(self, transaction):
        profile_id = transaction.properties.get('profile')
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


CREDIT_RULES['if'] = InviteFriend
