# -*- coding: utf-8 -*-
from mock import patch
from django_dynamic_fixture import G

from shoutit.models import (
    Message, Conversation, Notification, MessageRead, Profile)
from common.constants import (
    CONVERSATION_TYPE_CHAT, CONVERSATION_TYPE_PUBLIC_CHAT,
    NOTIFICATION_TYPE_READ_BY, NOTIFICATION_TYPE_STATS_UPDATE)
from tests.base import BaseTestCase, mocked_pusher


class MessagesDetailTestCase(BaseTestCase):
    url_name = 'message-detail'

    @classmethod
    def setUpTestData(cls):
        cls.user1 = cls.create_user()
        cls.user2 = cls.create_user(username='john')
        cls.c1 = G(Conversation, type=CONVERSATION_TYPE_CHAT)
        cls.c1.users.add(cls.user2)

    def test_message_delete_unknown_unauth(self):
        resp = self.client.delete(self.reverse(self.url_name,
                                               kwargs={'id': 1}))
        self.assert401(resp)

    def test_message_deleted(self):
        message = G(Message, user=self.user1, conversation=self.c1)
        self.client.login(username=self.user2.username, password='123')
        resp = self.client.delete(self.reverse(self.url_name,
                                               kwargs={'id': message.id}))
        self.assert204(resp)
        self.assertEqual(Message.objects.filter(user=self.user1).count(), 0)


class MessagesReadTestCase(BaseTestCase):
    url_name = 'message-read'

    @classmethod
    def setUpTestData(cls):
        cls.user1 = cls.create_user()
        cls.user2 = cls.create_user(username='john')
        cls.user3 = cls.create_user(username='mark')
        cls.user4 = cls.create_user(username='dark')
        cls.c1 = G(Conversation, type=CONVERSATION_TYPE_CHAT)
        cls.c1.users.add(cls.user2)
        cls.c2 = G(Conversation, type=CONVERSATION_TYPE_PUBLIC_CHAT,
                   creator=cls.user1, blocked=[cls.user4.pk])
        cls.m1 = G(Message, user=cls.user1, conversation=cls.c1)

    def test_message_read_unknown_unauth(self):
        """Forbidden for not registered user"""
        resp = self.client.post(self.reverse(self.url_name, kwargs={'id': 1}))
        self.assert401(resp)

    def test_message_not_contributor_forbidden(self):
        """Can't mark message as read for chat, if not participant"""
        self.client.login(username=self.user3.username, password='123')
        resp = self.client.post(self.reverse(self.url_name,
                                kwargs={'id': self.m1.pk}))
        self.assert403(resp)

    def test_message_not_contributor_public_allowed(self):
        """Resource is allowed for public conversation for registered user"""
        message = G(Message, user=self.user1, conversation=self.c2)
        self.client.login(username=self.user3.username, password='123')
        resp = self.client.post(self.reverse(self.url_name,
                                kwargs={'id': message.pk}))
        self.assert202(resp)

    def test_message_not_contributor_public_blocked(self):
        """Resource is forbidded for blockded user for public conversation"""
        message = G(Message, user=self.user1, conversation=self.c2)
        self.client.login(username=self.user4.username, password='123')
        resp = self.client.post(self.reverse(self.url_name,
                                kwargs={'id': message.pk}))
        self.assert403(resp)

    def test_message_mark_read(self):
        """Message marked as read for conversation participant"""
        Notification.objects.filter(to_user=self.user2).update(is_read=False)
        self.client.login(username=self.user2.username, password='123')
        resp = self.client.post(self.reverse(self.url_name,
                                kwargs={'id': self.m1.pk}))
        self.assert202(resp)
        self.assertTrue(Notification.objects.get(to_user=self.user2).is_read)
        message_read = MessageRead.objects.filter(
            user=self.user2, message=self.m1, conversation=self.c1)
        self.assertTrue(message_read.exists())

    @patch.object(mocked_pusher, 'trigger')
    def test_message_pusher_events(self, m_trigger):
        """Pusher events are triggered"""
        self.client.login(username=self.user2.username, password='123')
        m_trigger.reset_mock()
        self.client.post(self.reverse(self.url_name,
                         kwargs={'id': self.m1.pk}))
        self.assert_pusher_event(
            m_trigger, str(NOTIFICATION_TYPE_READ_BY),
            attached_object_partial_dict={'id': self.m1.id}, call_count=0)
        self.assert_pusher_event(
            m_trigger, str(NOTIFICATION_TYPE_STATS_UPDATE), call_count=1)

    def test_message_unread(self):
        """Read message marked as unread"""
        MessageRead.objects.get_or_create(user=self.user2, message=self.m1,
                                          conversation=self.c1)
        self.client.login(username=self.user2.username, password='123')
        resp = self.client.delete(self.reverse(self.url_name,
                                  kwargs={'id': self.m1.pk}))
        self.assert202(resp)
        self.assertEqual(MessageRead.objects.filter(user=self.user2).count(),
                         0)


class PublicChatsTestCase(BaseTestCase):
    url_name = 'public_chats-list'

    @classmethod
    def setUpTestData(cls):
        cls.user1 = cls.create_user()
        Profile.objects.filter(user=cls.user1).update(country='RU')
        cls.user2 = cls.create_user(username='john')
        Profile.objects.filter(user=cls.user2).update(country='RU')
        cls.user3 = cls.create_user(username='dark')
        Profile.objects.filter(user=cls.user3).update(country='US')
        cls.c1 = G(Conversation, type=CONVERSATION_TYPE_PUBLIC_CHAT,
                   creator=cls.user1, country='RU')
        cls.c2 = G(Conversation, type=CONVERSATION_TYPE_PUBLIC_CHAT,
                   creator=cls.user2, blocked=[cls.user2.pk], country='RU')
        cls.c3 = G(Conversation, type=CONVERSATION_TYPE_PUBLIC_CHAT,
                   creator=cls.user3, country='US')
        cls.c4 = G(Conversation, type=CONVERSATION_TYPE_CHAT)

    def test_public_chat_list_smoke(self):
        resp = self.client.get(self.reverse(self.url_name))
        self.assert401(resp)

    def test_public_chat_list_country_filter(self):
        """Public chats are filtered by user's country"""
        self.client.login(username=self.user1.username, password='123')
        resp = self.client.get(self.reverse(self.url_name))
        self.assert200(resp)
        self.assert_ids_equal(self.decode_json(resp)['results'],
                              [self.c1, self.c2])

    def test_public_chat_list_blocked_filter(self):
        """Public chats, where user is blocked, are filtered"""
        self.client.login(username=self.user2.username, password='123')
        resp = self.client.get(self.reverse(self.url_name))
        self.assert200(resp)
        self.assert_ids_equal(self.decode_json(resp)['results'],
                              [self.c1])

    def test_non_public_chat_create_forbidden(self):
        """Can't create non-public conversation"""
        self.client.login(username=self.user1.username, password='123')
        resp = self.client.post(
            self.reverse(self.url_name),
            {'subject': 'mychat', 'icon': '',
            'type': CONVERSATION_TYPE_CHAT.text})
        self.assert400(resp)

    def test_public_chat_created(self):
        """Public chat is created"""
        conversation = self._send_public_chat_create_request(
            self.user1, subject='mychat')
        self.assertEqual(conversation.subject, 'mychat')

    def test_public_chat_created_in_country(self):
        """Public chat is created with user's country"""
        conversation = self._send_public_chat_create_request(self.user1)
        self.assertEqual(
            conversation.location['country'],
            Profile.objects.get(user=self.user1).location['country'])

    def test_public_chat_created_another_country(self):
        """Public chat is created with user's country (US)"""
        # pass New York coordinates
        conversation = self._send_public_chat_create_request(
            self.user1,
            location={'latitude': 40.7141667, 'longitude': -74.0063889})
        self.assertEqual(conversation.location['country'], 'US')

    def test_public_chat_created_members(self):
        """Creator of public chat is chat member"""
        conversation = self._send_public_chat_create_request(self.user1)
        self.assertIn(self.user1, conversation.users.all())

    def test_public_chat_created_with_message(self):
        """Message is created automatically on public chat creation"""
        conversation = self._send_public_chat_create_request(self.user1)
        self.assertTrue(conversation.last_message.pk)

    def _send_public_chat_create_request(self, user, subject='mychat',
                                         icon='', **kwargs):
        self.client.login(username=user.username, password='123')
        req_data = {'subject': subject, 'icon': icon}
        req_data.update(kwargs)
        resp = self.client.post(self.reverse(self.url_name), req_data)
        self.assert201(resp)
        resp_data = self.decode_json(resp)
        return Conversation.objects.get(pk=resp_data['id'])
