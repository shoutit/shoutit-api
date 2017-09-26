# -*- coding: utf-8 -*-

from mock import patch
from django_dynamic_fixture import G, F

from common.constants import (
    CONVERSATION_TYPE_CHAT, CONVERSATION_TYPE_PUBLIC_CHAT,
    NOTIFICATION_TYPE_CONVERSATION_UPDATE, CONVERSATION_TYPE_ABOUT_SHOUT)
from shoutit.models import (
    Conversation, Message, MessageDelete, MessageRead, ConversationDelete
)
from tests.base import BaseTestCase, mocked_pusher
from .base import DetailMixin


class ConversationDetailTestCase(DetailMixin, BaseTestCase):
    url_name = 'conversation-detail'

    @classmethod
    def setUpTestData(cls):
        cls.user1 = cls.create_user()
        cls.user2 = cls.create_user(username='john')
        cls.user3 = cls.create_user(username='akakiy', is_active=False)
        cls.c1 = G(Conversation, type=CONVERSATION_TYPE_CHAT,
                   users=[cls.user1, cls.user3])
        cls.c2 = G(Conversation, type=CONVERSATION_TYPE_CHAT)
        cls.c3 = G(Conversation, type=CONVERSATION_TYPE_CHAT,
                   users=[cls.user1], blocked=[cls.user1.pk])
        cls.c4 = G(Conversation, type=CONVERSATION_TYPE_PUBLIC_CHAT,
                   creator=cls.user2, users=[cls.user1, cls.user2])

    def test_get_unauth(self):
        resp = self.client.get(self.get_url(1))
        self.assert401(resp)

    def test_detail_allowed_for_contributor(self):
        """
        Returned non-public chat details for contributor
        """
        self.login(self.user1)
        resp = self.client.get(self.get_url(self.c1.pk))
        self.assert200(resp)
        self.assert_ids_equal(self.decode_json(resp), self.c1)

    def test_detail_not_contributor_forbidden(self):
        """
        Access to non-public chat is forbidden to not contributor
        """
        self.login(self.user1)
        resp = self.client.get(self.get_url(self.c2.pk))
        self.assert403(resp)

    def test_detail_blocked_forbidden_even_if_contributor(self):
        """
        Conversation is invisible for blocked user, even if he is conributor
        """
        self.login(self.user1)
        resp = self.client.get(self.get_url(self.c3.pk))
        self.assert404(resp)

    def test_detail_public_chat_allowed(self):
        """
        Access to public chat allowed for non-blocked, non-contributor user
        """
        self.login(self.user1)
        resp = self.client.get(self.get_url(self.c4.pk))
        self.assert200(resp)
        self.assert_ids_equal(self.decode_json(resp), self.c4)

    def test_detail_public_chat_with_shout(self):
        """
        Chat with type 'about_shout' shows shout details
        """
        user = self.user1
        shout = self.create_shout(user=user,
                                  category=F(slug='velo'),
                                  item=F(name='Marin'))
        conv = G(Conversation,
                 type=CONVERSATION_TYPE_ABOUT_SHOUT,
                 creator=user)
        conv.attached_object = shout
        conv.users.add(user)
        conv.save()
        self.login(user)
        resp = self.client.get(self.get_url(conv.pk))
        self.assert200(resp)
        about = self.decode_json(resp)['about']
        self.assertEqual(about['title'], 'Marin')
        self.assertEqual(about['category']['slug'], 'velo')

    def test_detail_conversation_profiles(self):
        """
        User profiles are shown for conversation (including not active)
        """
        self.login(self.user1)
        resp = self.client.get(self.get_url(self.c1.pk))
        resp_ids = [p['id'] for p in self.decode_json(resp)['profiles']]
        self.assertEqual(set(resp_ids), set(['', str(self.user1.id)]))
        self.decode_json(resp)['profiles']

    def test_update_subject(self):
        """
        Conversation creator can update subject, using method PATCH
        """
        conv = G(Conversation, type=CONVERSATION_TYPE_CHAT, creator=self.user1)
        conv.users.add(self.user2)
        self.login(self.user1)
        resp = self.client.patch(self.get_url(conv.pk), {'subject': '-'})
        self.assert200(resp)
        self.assertEqual(Conversation.objects.get(pk=conv.pk).subject, '-')

    def test_update_icon(self):
        conv = G(Conversation, type=CONVERSATION_TYPE_CHAT, creator=self.user1)
        self.login(self.user1)
        icon_url = 'http://example.com/img.jpg'
        resp = self.client.patch(self.get_url(conv.pk), {'icon': icon_url})
        self.assert200(resp)
        conv.refresh_from_db()
        self.assertEqual(conv.icon, icon_url)

    @patch.object(mocked_pusher, 'trigger')
    def test_update_subject_pusher_event(self, m_trigger):
        """
        On conversation update event is sent to pusher
        """
        conv = G(Conversation, type=CONVERSATION_TYPE_CHAT, creator=self.user1)
        conv.users.add(self.user2)
        self.login(self.user1)
        m_trigger.reset_mock()
        self.client.patch(self.get_url(conv.pk), {'subject': '-'})
        self.assert_pusher_event(
            m_trigger, str(NOTIFICATION_TYPE_CONVERSATION_UPDATE),
            attached_object_partial_dict={'id': str(conv.id)})

    def test_update_subject_on_conversation_with_only_creator(self):
        """
        Conversation with only creator can be updated
        """
        conv = G(Conversation, type=CONVERSATION_TYPE_CHAT, creator=self.user1)
        self.login(self.user1)
        resp = self.client.patch(self.get_url(conv.pk), {'subject': '-'})
        self.assert200(resp)
        self.assertEqual(Conversation.objects.get(pk=conv.pk).subject, '-')

    def test_delete_conversation(self):
        """
        Conversation creator can delete conversation
        """
        conv = G(Conversation, type=CONVERSATION_TYPE_CHAT, creator=self.user1,
                 users=[self.user1])
        self.login(self.user1)
        resp = self.client.delete(self.get_url(conv.pk))
        self.assert204(resp)

    def test_delete_conversation_marked_as_deleted(self):
        """
        Deleted conversation is marked as deleted
        """
        conv = G(Conversation, type=CONVERSATION_TYPE_CHAT, creator=self.user1)
        conv.users.add(self.user1)
        self.login(self.user1)
        self.client.delete(self.get_url(conv.pk))
        self.assertEqual(
            ConversationDelete.objects.filter(conversation=conv).count(), 1)

    def test_user_is_excluded_from_deleted_conversation(self):
        """
        After user has delete the conversation, he is excluded from
        conversation contributors
        """
        conv = G(Conversation, type=CONVERSATION_TYPE_CHAT, creator=self.user1,
                 users=[self.user1, self.user2])
        self.login(self.user2)
        self.client.delete(self.get_url(conv.pk))
        self.assertNotIn(self.user2,
                         Conversation.objects.get(pk=conv.pk).users.all())

    def test_delete_conversation_messages_marked_read(self):
        """
        Messages of deleted conversation become read
        """
        conv = G(Conversation, type=CONVERSATION_TYPE_CHAT, creator=self.user1,
                 users=[self.user1, self.user2])
        m = G(Message, user=self.user2, conversation=conv)
        self.login(self.user1)
        self.client.delete(self.get_url(conv.pk))
        self.assertEqual(
            MessageRead.objects.filter(
                user=self.user1, message=m, conversation=conv).count(), 1)

    def test_delete_conversation_for_non_admin_is_allowed(self):
        """
        Non-admin contributor can't delete conversation
        """
        conv = G(Conversation, type=CONVERSATION_TYPE_CHAT, creator=self.user1,
                 users=[self.user1, self.user2])
        self.login(self.user2)
        resp = self.client.delete(self.get_url(conv.pk))
        self.assert204(resp)


class ConversationDeleteMessagesTestCase(DetailMixin, BaseTestCase):
    url_name = 'conversation-delete-messages'

    @classmethod
    def setUpTestData(cls):
        cls.user1 = cls.create_user()
        cls.user2 = cls.create_user(username='john')
        cls.c1 = G(Conversation, type=CONVERSATION_TYPE_CHAT,
                   creator=cls.user1, users=[cls.user1])
        cls.c2 = G(Conversation, type=CONVERSATION_TYPE_CHAT,
                   creator=cls.user1, users=[cls.user1])

    def test_get_unknown_unauth(self):
        resp = self.client.post(self.get_url(1))
        self.assert401(resp)

    def test_delete_messages(self):
        """
        Requested messages are marked as deleted for user from request.
        """
        m1 = G(Message, user=self.user1, conversation=self.c1)
        m2 = G(Message, user=self.user2, conversation=self.c1)
        self.login(self.user1)
        resp = self.client.post(self.get_url(self.c1.pk), {'messages': [
            {'id': m1.id}, {'id': m2.id},
        ]})
        self.assert202(resp)
        self.assertEqual(MessageDelete.objects.count(), 2)
        self.assertEqual(
            set(MessageDelete.objects.values_list(
                'user_id', 'message_id', 'conversation_id')),
            set([(self.user1.id, m1.id, self.c1.id),
                 (self.user1.id, m2.id, self.c1.id)]))

    def test_delete_messages_other_conversation_excluded(self):
        """
        Messages from other conversation is ignored for marking as deleted.
        """
        m1 = G(Message, user=self.user1, conversation=self.c1)
        m2 = G(Message, user=self.user1, conversation=self.c2)
        self.login(self.user1)
        resp = self.client.post(self.get_url(self.c1.pk), {'messages': [
            {'id': m1.id}, {'id': m2.id},
        ]})
        self.assert202(resp)
        self.assertEqual(MessageDelete.objects.count(), 1)
        self.assertEqual(
            set(MessageDelete.objects.values_list(
                'user_id', 'message_id', 'conversation_id')),
            set([(self.user1.id, m1.id, self.c1.id)]))
