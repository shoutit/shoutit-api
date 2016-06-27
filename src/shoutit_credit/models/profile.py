"""

"""
from __future__ import unicode_literals

import random
import string

from django.conf import settings
from django.db import models
from django.db.models import Q, F
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.translation import ugettext_lazy as _
from django_rq import job
from hvad.manager import TranslationManager

from common.constants import LISTEN_TYPE_PROFILE, LISTEN_TYPE_PAGE
from shoutit.models import User, Profile, Listen2, ProfileContact, UUIDModel
from .base import CreditRule, CreditTransaction

complete_profile = None
invite_friends = None
listen_to_friends = None

INVITATION_CODE_MAX_USAGE = 10


class CompleteProfileManager(TranslationManager):
    def get_queryset(self):
        return super(CompleteProfileManager, self).get_queryset().filter(type='complete_profile')


class CompleteProfile(CreditRule):
    text = _("You earned 1 Shoutit Credit for completing your profile.")

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

        # Terms and conditions apply!
        not_guest = not profile.user.is_guest
        has_token = profile.user.accesstoken_set.exists()
        completed_profile = all([profile.image is not None, profile.gender is not None, profile.birthday is not None])

        if not all([not_guest, has_token, completed_profile]):
            return

        # Create Credit Transaction
        transaction = CreditTransaction.create(user_id=profile.user_id, amount=1, rule=self)
        return transaction


@job(settings.RQ_QUEUE_CREDIT)
def apply_complete_profile(profile):
    global complete_profile
    if not complete_profile:
        complete_profile = CompleteProfile.objects.first()
    if complete_profile:
        complete_profile.apply(profile)


@receiver(post_save, sender=Profile)
def profile_post_save(sender, instance=None, created=False, update_fields=None, **kwargs):
    apply_complete_profile.delay(instance)


class InviteFriendsManager(TranslationManager):
    def get_queryset(self):
        return super(InviteFriendsManager, self).get_queryset().filter(type='invite_friends')


class InviteFriends(CreditRule):
    """
    Transactions of this rule must have: `profile_id`
    """
    text = _("You earned 1 Shoutit Credit for inviting %(name)s.")

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
        text = self.text % {'name': name}
        ret = {
            "text": text,
            "ranges": [{'offset': text.index(name), 'length': len(name)}]
        }
        return ret

    def apply(self, user, code):
        invitation_code = InvitationCode.objects.filter(code=code, used_count__lt=INVITATION_CODE_MAX_USAGE).first()
        if not invitation_code or not invitation_code.is_active:
            return

        # Create Credit Transaction
        properties = {'profile_id': user.pk}
        transaction = CreditTransaction.create(user=invitation_code.user, amount=1, rule=self, properties=properties)
        # Update the invitation code
        InvitationCode.objects.filter(id=invitation_code.id).update(used_count=F('used_count') + 1)
        return transaction


@job(settings.RQ_QUEUE_CREDIT)
def _apply_invite_friends(user, code):
    global invite_friends
    if not invite_friends:
        invite_friends = InviteFriends.objects.first()
    if invite_friends:
        invite_friends.apply(user, code)


def apply_invite_friends(user, code):
    _apply_invite_friends.delay(user, code)


class ListenToFriendsManager(TranslationManager):
    def get_queryset(self):
        return super(ListenToFriendsManager, self).get_queryset().filter(type='listen_to_friends')


class ListenToFriends(CreditRule):
    text = _("You earned %(amount)d Shoutit Credit for listening to your friends.")
    max_listens = 3

    objects = ListenToFriendsManager()

    class Meta:
        proxy = True

    def display(self, transaction):
        text = self.text % {'amount': abs(transaction.amount)}
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
    global listen_to_friends
    if not listen_to_friends:
        listen_to_friends = ListenToFriends.objects.first()
    if listen_to_friends:
        listen_to_friends.apply(listen)


@receiver(post_save, sender=Listen2)
def listen_post_save(sender, instance=None, created=False, update_fields=None, **kwargs):
    if instance.type in [LISTEN_TYPE_PROFILE, LISTEN_TYPE_PAGE]:
        apply_listen_to_friends.delay(instance)


class InvitationCode(UUIDModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='invitation_codes')
    code = models.CharField(max_length=10, unique=True)
    used_count = models.SmallIntegerField(default=0)
    is_active = models.BooleanField(default=True)


@property
def user_invitation_code(self):
    invitation_code = self.invitation_codes.filter(is_active=True).first()
    if invitation_code:
        if invitation_code.used_count >= INVITATION_CODE_MAX_USAGE:
            invitation_code.update(is_active=False)
        else:
            return invitation_code
    code = code_generator()
    return InvitationCode.create(user=self, code=code)


User.add_to_class('invitation_code', user_invitation_code)


def code_generator(size=10, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))
