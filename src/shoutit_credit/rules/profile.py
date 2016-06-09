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


CREDIT_RULES['complete_profile'] = CompleteProfile


class InviteFriends(CreditRule):
    """
    Transactions of this rule must have: `profile_id`
    """
    text = "You earned 1 credit for inviting %s."

    class Meta:
        proxy = True

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


CREDIT_RULES['invite_friends'] = InviteFriends


class ListenToFriends(CreditRule):
    text = "You earned %d credit for listening to your friends."

    class Meta:
        proxy = True

    def display(self, transaction):
        text = self.text % transaction.amount
        ret = {
            "text": text,
            "ranges": []
        }
        return ret


CREDIT_RULES['listen_to_friends'] = ListenToFriends
