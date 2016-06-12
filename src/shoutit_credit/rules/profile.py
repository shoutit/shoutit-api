"""

"""
from __future__ import unicode_literals

from django.conf import settings
from django.db import models
from django.db.models import Q
from django.db.models.signals import post_save
from django.dispatch import receiver
from django_rq import job

from shoutit.models import User, Profile, Listen2, ProfileContact
from ..models import CreditRule, CREDIT_RULES, CreditTransaction

complete_profile = None
invite_friends = None
listen_to_friends = None


class CompleteProfileManager(models.Manager):
    def get_queryset(self):
        return super(CompleteProfileManager, self).get_queryset().filter(type='complete_profile')


class CompleteProfile(CreditRule):
    text = "You earned 1 Shoutit Credit for completing your profile."

    objects = CompleteProfileManager()

    class Meta:
        proxy = True

    def display(self, transaction):
        setattr(transaction, 'target', transaction.user)
        ret = {
            "text": self.text,
            "ranges": []
        }
        return ret

    def apply(self, profile):
        # Check for similar existing transaction
        if CreditTransaction.exists(user_id=profile.user_id, rule=self):
            return

        # Create Credit Transaction
        transaction = CreditTransaction.create(user_id=profile.user_id, amount=1, rule=self)
        return transaction


@job(settings.RQ_QUEUE_CREDIT)
def apply_complete_profile(profile):
    complete_profile.apply(profile)


@receiver(post_save, sender=Profile)
def profile_post_save(sender, instance=None, created=False, update_fields=None, **kwargs):
    apply_complete_profile.delay(instance)


class InviteFriendsManager(models.Manager):
    def get_queryset(self):
        return super(InviteFriendsManager, self).get_queryset().filter(type='invite_friends')


class InviteFriends(CreditRule):
    """
    Transactions of this rule must have: `profile_id`
    """
    text = "You earned 1 Shoutit Credit for inviting %s."

    objects = InviteFriendsManager()

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

    def apply(self, user):
        invited_by = getattr(user, 'invited_by', None)
        if not invited_by:
            return

        # Create Credit Transaction
        properties = {'profile_id': user.pk}
        transaction = CreditTransaction.create(user_id=invited_by, amount=1, rule=self, properties=properties)
        return transaction


@job(settings.RQ_QUEUE_CREDIT)
def apply_invite_friends(user):
    invite_friends.apply(user)


@receiver(post_save, sender=User)
def user_post_save(sender, instance=None, created=False, update_fields=None, **kwargs):
    if created:
        apply_listen_to_friends.delay(instance)


class ListenToFriendsManager(models.Manager):
    def get_queryset(self):
        return super(ListenToFriendsManager, self).get_queryset().filter(type='listen_to_friends')


class ListenToFriends(CreditRule):
    text = "You earned %d Shoutit Credit for listening to your friends."
    max_listens = 3

    objects = ListenToFriendsManager()

    class Meta:
        proxy = True

    def display(self, transaction):
        text = self.text % abs(transaction.amount)
        ret = {
            "text": text,
            "ranges": []
        }
        return ret

    def apply(self, listen):
        user_id = listen.user_id
        target_id = listen.target

        # Check for similar existing transaction
        if CreditTransaction.exists(user_id=user_id, rule=self, properties__at_profile_id=target_id):
            return

        # Check for count of similar transactions
        similar_count = CreditTransaction.objects.filter(user_id=user_id, rule=self).count()
        if similar_count >= self.max_listens:
            return

        # Check where the target is one of the user's contacts
        lookup = Q()
        target_email = User.objects.filter(id=target_id).values_list('email', flat=True).first()
        if target_email:
            lookup |= Q(emails__contains=[target_email])

        target_mobile = Profile.objects.filter(id=target_id).values_list('mobile', flat=True).first()
        if target_mobile:
            lookup |= Q(mobiles__contains=[target_mobile])

        if not ProfileContact.exists(Q(user_id=user_id) & lookup):
            return

        # Create Credit Transaction
        properties = {'profile_id': target_id}
        transaction = CreditTransaction.create(user_id=user_id, amount=1, rule=self, properties=properties)
        return transaction


@job(settings.RQ_QUEUE_CREDIT)
def apply_listen_to_friends(listen):
    listen_to_friends.apply(listen)


@receiver(post_save, sender=Listen2)
def listen_post_save(sender, instance=None, created=False, update_fields=None, **kwargs):
    apply_listen_to_friends.delay(instance)


def map_rules():
    import sys
    # Todo (mo): This doesn't look good, Find more general way of mapping rules

    CREDIT_RULES['complete_profile'] = CompleteProfile
    _complete_profile = CompleteProfile.objects.first()
    setattr(sys.modules[__name__], 'complete_profile', _complete_profile)

    CREDIT_RULES['invite_friends'] = InviteFriends
    _invite_friends = InviteFriends.objects.first()
    setattr(sys.modules[__name__], 'invite_friends', _invite_friends)

    CREDIT_RULES['listen_to_friends'] = ListenToFriends
    _listen_to_friends = ListenToFriends.objects.first()
    setattr(sys.modules[__name__], 'listen_to_friends', _listen_to_friends)
