# -*- coding: utf-8 -*-
from django_dynamic_fixture import G

from common.constants import CONVERSATION_TYPE_CHAT
from shoutit.models import Conversation


class DetailMixin(object):

    @classmethod
    def get_url(cls, conversation_id):
        return cls.reverse(cls.url_name, kwargs={'id': conversation_id})


class AttachmentsMixin(object):
    @classmethod
    def setUpTestData(cls):
        cls.user1 = cls.create_user(country='RU')
        cls.c1 = G(Conversation, type=CONVERSATION_TYPE_CHAT,
                   creator=cls.user1, country='RU', users=[cls.user1])

    def test_get_unknown_unauth(self):
        resp = self.client.get(self.get_url(1))
        self.assert401(resp)

    def test_no_message_meida_attachments(self):
        """
        Result data is empty when no attachments exists
        """
        self.login(self.user1)
        resp = self.client.get(self.get_url(self.c1.pk))
        self.assert200(resp)
        self.assertEqual(self.decode_json(resp)['results'], [])
