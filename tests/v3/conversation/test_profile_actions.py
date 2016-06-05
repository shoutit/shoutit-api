# -*- coding: utf-8 -*-
from mock import patch
from django_dynamic_fixture import G

from common.constants import (
    CONVERSATION_TYPE_CHAT, NOTIFICATION_TYPE_CONVERSATION_UPDATE,
    LISTEN_TYPE_PROFILE
)
from shoutit.models import Conversation, Listen2
from tests.base import BaseTestCase, mocked_pusher
from .base import DetailMixin


class ProfileMixin(DetailMixin):

    @classmethod
    def setUpTestData(cls):
        cls.user1 = BaseTestCase.create_user()
        cls.user2 = BaseTestCase.create_user(username='john')
        cls.c1 = G(Conversation, type=CONVERSATION_TYPE_CHAT,
                   creator=cls.user1, users=[cls.user1, cls.user2])
        cls.valid_user = cls.user2

    def test_get_unknown_unauth(self):
        resp = self.do_request(1, self.user1)
        self.assert401(resp)

    def test_non_admin_is_forbidden(self):
        """
        Non-admin contributor can't make action with profile
        """
        self.login(self.valid_user)
        resp = self.do_request(self.c1.pk, self.user1)
        self.assert403(resp)

    def test_action_on_current_user_profile_is_forbidden(self):
        """
        It is forbidden to make action on current user profile
        """
        self.login(self.user1)
        resp = self.do_request(self.c1.pk, self.user1)
        self.assert400(resp)

    @patch.object(mocked_pusher, 'trigger')
    def test_profile_action_conversation_update_pusher_event(self, m_trigger):
        """
        Conversation update event is sent to pusher on profile action
        """
        self.login(self.user1)
        m_trigger.reset_mock()
        self.do_request(self.c1.pk, self.valid_user)
        self.assert_pusher_event(
            m_trigger, str(NOTIFICATION_TYPE_CONVERSATION_UPDATE),
            attached_object_partial_dict={'id': str(self.c1.id)})

    def do_request(self, conversation_id, user):
        return self.client.post(self.get_url(conversation_id), {
            'profile': {'id': user.profile.id}
        })


class ConversationAddProfileTestCase(ProfileMixin, BaseTestCase):
    url_name = 'conversation-add-profile'

    @classmethod
    def setUpTestData(cls):
        ProfileMixin.setUpTestData()
        cls.user3 = cls.create_user(username='dmitry')
        cls.user4 = cls.create_user(username='viktor')
        G(Listen2, user=cls.user3, type=int(LISTEN_TYPE_PROFILE),
          target=cls.user1.id)
        G(Listen2, user=cls.user3, type=int(LISTEN_TYPE_PROFILE),
          target=cls.user2.id)
        cls.valid_user = cls.user3

    def test_not_listening_profile_is_forbidden(self):
        """
        It is forbidden to add profile, that is not listening to current user
        """
        self.login(self.user1)
        resp = self.do_request(self.c1.pk, self.user4)
        self.assert400(resp)
        self.assertNotIn(self.user4, self.c1.users.all())

    def test_profile_added_to_conversation(self):
        """
        Profile is added to conversation
        """
        self.login(self.user1)
        resp = self.do_request(self.c1.pk, self.valid_user)
        self.assert202(resp)
        self.assertIn(self.valid_user, self.c1.users.all())

    def test_add_already_added_profile(self):
        """
        It is allowed to add user that is already a contributor
        """
        self.c1.users.add(self.valid_user)
        self.c1.save()
        self.login(self.user1)
        resp = self.do_request(self.c1.pk, self.valid_user)
        self.assert202(resp)


class ConversationRemoveProfileTestCase(ProfileMixin, BaseTestCase):
    url_name = 'conversation-remove-profile'

    def test_profile_is_removed(self):
        """
        Profile is removed from conversation
        """
        self.login(self.user1)
        resp = self.do_request(self.c1.pk, self.valid_user)
        self.assert202(resp)
        self.assertNotIn(self.valid_user, self.c1.users.all())


class ConversationPromoteAdminTestCase(ProfileMixin, BaseTestCase):
    url_name = 'conversation-promote-admin'

    def test_promote_admin(self):
        """
        User successfully added to conversation admins
        """
        self.login(self.user1)
        resp = self.do_request(self.c1.pk, self.valid_user)
        self.assert202(resp)
        self.assertIn(self.valid_user.id,
                      Conversation.objects.get(pk=self.c1.pk).admins)

    def test_promote_non_contributor_is_forbidden(self):
        """
        It is forbidden to promote non-contributer user as admin
        """
        non_contributor = self.create_user(username='dorn')
        self.login(self.user1)
        resp = self.do_request(self.c1.pk, non_contributor)
        self.assert400(resp)
        self.assertNotIn(non_contributor.id,
                         Conversation.objects.get(pk=self.c1.pk).admins)

    def test_promote_already_admin(self):
        """
        It is allowed to promote a user that is already admin
        """
        self.c1.admins.append(self.valid_user.id)
        self.c1.save()
        self.login(self.user1)
        resp = self.do_request(self.c1.pk, self.valid_user)
        self.assert202(resp)


class ConversationBlockProfileTestCase(ProfileMixin, BaseTestCase):
    url_name = 'conversation-block-profile'

    def test_block_user(self):
        """
        User successfully added to blocked users
        """
        self.login(self.user1)
        resp = self.do_request(self.c1.pk, self.valid_user)
        self.assert202(resp)
        self.assertIn(self.valid_user.profile.id,
                      Conversation.objects.get(pk=self.c1.pk).blocked)

    def test_block_non_contributor_is_forbidden(self):
        """
        It is forbidden to block non-contributer user
        """
        non_contributor = self.create_user(username='dorn')
        self.login(self.user1)
        resp = self.do_request(self.c1.pk, non_contributor)
        self.assert400(resp)
        self.assertNotIn(non_contributor.profile.id,
                         Conversation.objects.get(pk=self.c1.pk).blocked)

    def test_block_already_blocked_user(self):
        """
        It is allowed to block already blocked user
        """
        self.c1 = Conversation.objects.get(pk=self.c1.pk)
        self.c1.blocked.append(self.valid_user.profile.id)
        self.c1.save()
        self.login(self.user1)
        resp = self.do_request(self.c1.pk, self.valid_user)
        self.assert202(resp)

    def test_blocked_user_is_no_more_admin(self):
        """
        If blocked user was an admin, he is no more
        """
        self.c1 = Conversation.objects.get(pk=self.c1.pk)
        self.c1.admins.append(self.valid_user.profile.id)
        self.c1.save()
        self.login(self.user1)
        resp = self.do_request(self.c1.pk, self.valid_user)
        self.assert202(resp)
        self.assertNotIn(self.valid_user.profile.id,
                         Conversation.objects.get(pk=self.c1.pk).admins)


class ConversationUnblockProfileTestCase(ProfileMixin, BaseTestCase):
    url_name = 'conversation-unblock-profile'

    @classmethod
    def setUpTestData(cls):
        ProfileMixin.setUpTestData()
        cls.user3 = cls.create_user(username='dmitry')
        cls.c1.users.add(cls.user3)
        cls.c1.blocked.append(cls.valid_user.id)
        cls.c1.save()

    def test_non_admin_is_forbidden(self):
        """
        Non-admin contributor can't make action with profile
        """
        self.login(self.user3)
        resp = self.do_request(self.c1.pk, self.user1)
        self.assert403(resp)

    def test_unblock_user(self):
        """
        User successfully removed from blocked users
        """
        self.login(self.user1)
        resp = self.do_request(self.c1.pk, self.valid_user)
        self.assert202(resp)
        self.assertNotIn(self.valid_user.id,
                         Conversation.objects.get(pk=self.c1.pk).blocked)

    def test_unblock_non_blocked_user_is_forbidden(self):
        """
        It is forbidden to unblock non-blocked user
        """
        self.login(self.user1)
        resp = self.do_request(self.c1.pk, self.user3)
        self.assert400(resp)
