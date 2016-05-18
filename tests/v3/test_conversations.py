# -*- coding: utf-8 -*-
from tests.base import BaseTestCase


class ConversationTestCase(BaseTestCase):
    url_name = 'conversation-list'

    def test_get_list_unauth(self):
        resp = self.client.get(self.reverse(self.url_name))
        self.assert401(resp)


class ConversationDetailTestCase(BaseTestCase):
    url_name = 'conversation-detail'

    def test_get_unknown_unauth(self):
        resp = self.client.get(self.reverse(self.url_name, kwargs={'id': 1}))
        self.assert401(resp)


class ConversationAddProfileTestCase(BaseTestCase):
    url_name = 'conversation-add-profile'

    def test_get_unknown_unauth(self):
        resp = self.client.get(self.reverse(self.url_name, kwargs={'id': 1}))
        self.assert401(resp)


class ConversationDeleteMessagesTestCase(BaseTestCase):
    url_name = 'conversation-delete-messages'

    def test_get_unknown_unauth(self):
        resp = self.client.get(self.reverse(self.url_name, kwargs={'id': 1}))
        self.assert401(resp)


class ConversationMessagesTestCase(BaseTestCase):
    url_name = 'conversation-messages'

    def test_get_unknown_unauth(self):
        resp = self.client.get(self.reverse(self.url_name, kwargs={'id': 1}))
        self.assert401(resp)


class ConversationPromoteAdminTestCase(BaseTestCase):
    url_name = 'conversation-promote-admin'

    def test_get_unknown_unauth(self):
        resp = self.client.get(self.reverse(self.url_name, kwargs={'id': 1}))
        self.assert401(resp)


class ConversationReadTestCase(BaseTestCase):
    url_name = 'conversation-read'

    def test_get_unknown_unauth(self):
        resp = self.client.get(self.reverse(self.url_name, kwargs={'id': 1}))
        self.assert401(resp)


class ConversationRemoveProfileTestCase(BaseTestCase):
    url_name = 'conversation-remove-profile'

    def test_get_unknown_unauth(self):
        resp = self.client.get(self.reverse(self.url_name, kwargs={'id': 1}))
        self.assert401(resp)


class ConversationReplyProfileTestCase(BaseTestCase):
    url_name = 'conversation-reply'

    def test_get_unknown_unauth(self):
        resp = self.client.get(self.reverse(self.url_name, kwargs={'id': 1}))
        self.assert401(resp)


class ConversationBlockProfileTestCase(BaseTestCase):
    url_name = 'conversation-block-profile'

    def test_get_unknown_unauth(self):
        resp = self.client.get(self.reverse(self.url_name, kwargs={'id': 1}))
        self.assert401(resp)


class ConversationBlockedTestCase(BaseTestCase):
    url_name = 'conversation-blocked'

    def test_get_unknown_unauth(self):
        resp = self.client.get(self.reverse(self.url_name, kwargs={'id': 1}))
        self.assert401(resp)


class ConversationMediaTestCase(BaseTestCase):
    url_name = 'conversation-media'

    def test_get_unknown_unauth(self):
        resp = self.client.get(self.reverse(self.url_name, kwargs={'id': 1}))
        self.assert401(resp)


class ConversationShoutsTestCase(BaseTestCase):
    url_name = 'conversation-shouts'

    def test_get_unknown_unauth(self):
        resp = self.client.get(self.reverse(self.url_name, kwargs={'id': 1}))
        self.assert401(resp)


class ConversationUnblockProfileTestCase(BaseTestCase):
    url_name = 'conversation-unblock-profile'

    def test_get_unknown_unauth(self):
        resp = self.client.get(self.reverse(self.url_name, kwargs={'id': 1}))
        self.assert401(resp)
