# -*- coding: utf-8 -*-
from django_dynamic_fixture import G, F

from common.constants import (
    CONVERSATION_TYPE_CHAT, MESSAGE_ATTACHMENT_TYPE_MEDIA,
    MESSAGE_ATTACHMENT_TYPE_SHOUT
)
from shoutit.models import (
    Conversation, Message, MessageDelete, MessageAttachment
)
from shoutit.models.auth import APNSDevice
from tests.base import BaseTestCase
from .base import DetailMixin, AttachmentsMixin


class ConversationMessagesTestCase(DetailMixin, BaseTestCase):
    url_name = 'conversation-messages'

    @classmethod
    def setUpTestData(cls):
        cls.user1 = cls.create_user(country='RU')
        cls.user2 = cls.create_user(username='john', country='US')
        cls.device = G(APNSDevice, user=cls.user1)
        cls.c1 = G(Conversation, type=CONVERSATION_TYPE_CHAT,
                   creator=cls.user1, country='RU', users=[cls.user1])

    def test_get_unknown_unauth(self):
        resp = self.client.get(self.get_url(1))
        self.assert401(resp)

    def test_conversation_messages_deleted_messages_excluded(self):
        """
        Deleted messages are not present in response
        """
        m1 = G(Message, user=self.user1, conversation=self.c1)
        m2 = G(Message, user=self.user1, conversation=self.c1)
        G(MessageDelete, user=self.user1, message=m2, conversation=self.c1)
        self.login(self.user1)
        resp = self.client.get(self.get_url(self.c1.pk))
        self.assert200(resp)
        self.assert_ids_equal(self.decode_json(resp)['results'], [m1])


class ConversationMediaTestCase(DetailMixin, AttachmentsMixin, BaseTestCase):
    url_name = 'conversation-media'

    def test_message_media_attachments(self):
        """
        Result contains message attachments linked to requested conversation
        """
        m = G(Message, user=self.user1, conversation=self.c1)
        G(MessageAttachment, type=MESSAGE_ATTACHMENT_TYPE_MEDIA,
          message=m, conversation=self.c1,
          images=['http://s3.com/media.png'],
          videos=[F(url='http://yout.com/abc')])
        G(MessageAttachment, type=MESSAGE_ATTACHMENT_TYPE_SHOUT,
          message=m, conversation=self.c1)
        self.login(self.user1)
        resp = self.client.get(self.get_url(self.c1.pk))
        self.assert200(resp)
        resp_results = self.decode_json(resp)['results']
        self.assertEqual(len(resp_results), 1)
        self.assertEqual(resp_results[0]['images'], ['http://s3.com/media.png'])
        self.assertEqual([v['url'] for v in resp_results[0]['videos']],
                         ['http://yout.com/abc'])
        # only media fields are present
        self.assertFalse(set(resp_results[0].keys()) &
                         set(['shout', 'location', 'profile']))


class ConversationShoutsTestCase(DetailMixin, AttachmentsMixin, BaseTestCase):
    url_name = 'conversation-shouts'

    def test_message_shout_attachments(self):
        """
        Result contains distinct shouts that has message attachments,
        linked to requested conversation
        """
        c2 = G(Conversation, type=CONVERSATION_TYPE_CHAT, creator=self.user1)
        m1 = G(Message, user=self.user1, conversation=self.c1)
        m2 = G(Message, user=self.user1, conversation=c2)
        shout1 = self.create_shout(
            user=self.user1, category=F(name='velo'), item=F(name='Marin'))
        shout2 = self.create_shout(
            user=self.user1, category=F(name='flower'), item=F(name='Rose'))
        shout1.message_attachments.add(
            G(MessageAttachment, type=MESSAGE_ATTACHMENT_TYPE_SHOUT,
              message=m1, conversation=self.c1),
            G(MessageAttachment, type=MESSAGE_ATTACHMENT_TYPE_SHOUT,
              message=m1, conversation=self.c1),
        )
        shout2.message_attachments.add(
            G(MessageAttachment, type=MESSAGE_ATTACHMENT_TYPE_SHOUT,
              message=m2, conversation=c2)
        )
        self.login(self.user1)
        resp = self.client.get(self.get_url(self.c1.pk))
        self.assert200(resp)
        self.assert_ids_equal(self.decode_json(resp)['results'], [shout1])


class ConversationBlockedTestCase(DetailMixin, BaseTestCase):
    url_name = 'conversation-blocked'

    @classmethod
    def setUpTestData(cls):
        cls.user1 = BaseTestCase.create_user()
        cls.user2 = BaseTestCase.create_user(username='john')
        cls.user3 = BaseTestCase.create_user(username='dorn')
        cls.c1 = G(Conversation, type=CONVERSATION_TYPE_CHAT,
                   creator=cls.user1, users=[cls.user1, cls.user2, cls.user3],
                   blocked=[cls.user3.pk])

    def test_get_unknown_unauth(self):
        resp = self.client.get(self.get_url(1))
        self.assert401(resp)

    def test_list_blocked_users(self):
        """
        Only blocked users are returned
        """
        self.login(self.user1)
        resp = self.client.get(self.get_url(self.c1.pk))
        self.assert200(resp)
        self.assert_ids_equal(self.decode_json(resp)['results'], [self.user3])
