# -*- coding: utf-8 -*-
import responses
from django_dynamic_fixture import G

from common.constants import (
    CONVERSATION_TYPE_CHAT, CONVERSATION_TYPE_PUBLIC_CHAT
)
from shoutit.models import Conversation, Message
from tests.base import BaseTestCase


class ConversationTestCase(BaseTestCase):
    url_name = 'conversation-list'

    @classmethod
    def setUpTestData(cls):
        cls.user1 = cls.create_user(country='RU')
        cls.user2 = cls.create_user(username='john', country='US')
        cls.user3 = cls.create_user(username='akakiy', country='RU')
        cls.c1 = G(Conversation, type=CONVERSATION_TYPE_CHAT,
                   users=[cls.user1, cls.user2])
        cls.c2 = G(Conversation, type=CONVERSATION_TYPE_PUBLIC_CHAT,
                   creator=cls.user1, country='RU')

    def test_get_list_unauth(self):
        resp = self.client.get(self.get_url())
        self.assert401(resp)

    def test_list_all_except_blocked(self):
        """
        Return all user's conversations, except blocked
        """
        conv = G(Conversation, type=CONVERSATION_TYPE_CHAT, creator=self.user1,
                 blocked=[self.user2.pk])
        conv.users.add(self.user2)
        self.login(self.user2)
        resp = self.client.get(self.get_url())
        self.assert200(resp)
        self.assert_ids_equal(self.decode_json(resp)['results'], [self.c1])

    def test_list_public_filtered_by_country(self):
        """
        Return public chats, filtered by country
        """
        conv_US = G(Conversation, type=CONVERSATION_TYPE_PUBLIC_CHAT,
                    creator=self.user1, country='US')
        self.login(self.user2)
        resp = self.client.get(self.get_url() + "?type=public_chat")
        self.assert200(resp)
        self.assert_ids_equal(self.decode_json(resp)['results'], [conv_US])

    def test_list_public_blocked_excluded(self):
        """
        Return public chats, filtered by country
        """
        G(Conversation, type=CONVERSATION_TYPE_PUBLIC_CHAT,
          creator=self.user2, country='RU', blocked=[self.user1.pk])
        self.login(self.user1)
        resp = self.client.get(self.get_url() + "?type=public_chat")
        self.assert200(resp)
        self.assert_ids_equal(self.decode_json(resp)['results'], [self.c2])

    def test_create_public_conversation(self):
        """
        Public conversation is created
        """
        self.login(self.user3)
        resp = self.client.post(self.get_url(), {'subject': 'Public chat'})
        self.assert201(resp)
        conv = Conversation.objects.get(pk=self.decode_json(resp)['id'])
        self.assertTrue(conv is not None)
        self.assertEqual(conv.type, CONVERSATION_TYPE_PUBLIC_CHAT)
        self.assertEqual(conv.subject, 'Public chat')

    def test_create_public_conversation_creator_assigned(self):
        """
        User that has created the conversation becomes a creator
        """
        self.login(self.user3)
        resp = self.client.post(self.get_url(), {'subject': 'Public chat'})
        conv = Conversation.objects.get(pk=self.decode_json(resp)['id'])
        self.assertEqual(conv.creator.pk, self.user3.pk)
        self.assertIn(self.user3.id, conv.admins)
        self.assertIn(self.user3, conv.users.all())

    def test_public_chat_message_created(self):
        """
        Message is created after creation of public conversation
        """
        self.login(self.user3)
        resp = self.client.post(self.get_url(), {'subject': 'Public chat'})
        conv = Conversation.objects.get(pk=self.decode_json(resp)['id'])
        self.assertTrue(Message.objects.filter(conversation=conv).exists())

    @responses.activate
    def test_create_public_conversation_with_location(self):
        """
        Provided location is assigned to created conversation
        """
        self.login(self.user3)
        data = {'subject': 'Public chat', 'location': self.COORDINATES['USA']}
        self.add_googleapis_geocode_response('us_new_york.json')
        resp = self.client.post(self.get_url(), data)
        conv = Conversation.objects.get(pk=self.decode_json(resp)['id'])
        self.assertEqual(conv.location['country'], 'US')

    def test_create_non_public_conversation_forbidden(self):
        """
        Non-public conversation creation is forbidden
        """
        self.login(self.user3)
        resp = self.client.post(
            self.get_url(),
            {'subject': 'Some subject', 'type': str(CONVERSATION_TYPE_CHAT)})
        self.assert400(resp)

    def get_url(cls):
        return cls.reverse(cls.url_name)
