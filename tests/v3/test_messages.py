# -*- coding: utf-8 -*-
from tests.base import BaseTestCase


class MessagesDetailTestCase(BaseTestCase):
    url_name = 'message-detail'

    def test_message_delete_unknown_unauth(self):
        resp = self.client.delete(self.reverse(self.url_name,
                                               kwargs={'id': 1}))
        self.assert401(resp)


class MessagesReadTestCase(BaseTestCase):
    url_name = 'message-read'

    def test_message_read_unknown_unauth(self):
        resp = self.client.post(self.reverse(self.url_name, kwargs={'id': 1}))
        self.assert401(resp)


class PublicChatsTestCase(BaseTestCase):
    url_name = 'public_chats-list'

    def test_publich_chats_list_smoke(self):
        resp = self.client.post(self.reverse(self.url_name))
        self.assert401(resp)
