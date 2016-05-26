# -*- coding: utf-8 -*-
from tests.base import BaseTestCase


class ProfileListTestCase(BaseTestCase):
    url_name = 'profile-list'

    def test_profile_list(self):
        resp = self.client.get(self.reverse(self.url_name))
        self.assert200(resp)


class ProfileDetailTestCase(BaseTestCase):
    url_name = 'profile-detail'

    def test_profile_detail_unknown(self):
        resp = self.client.get(
            self.reverse(self.url_name, kwargs={'username': 'unknown'}))
        self.assert404(resp)


class ProfileChatTestCase(BaseTestCase):
    url_name = 'profile-chat'

    def test_profile_chat_unknown(self):
        resp = self.client.post(
            self.reverse(self.url_name, kwargs={'username': 'unknown'}))
        self.assert401(resp)


class ProfileDeactivateTestCase(BaseTestCase):
    url_name = 'profile-deactivate'

    def test_profile_deactivate_unknown(self):
        resp = self.client.post(
            self.reverse(self.url_name, kwargs={'username': 'unknown'}))
        self.assert401(resp)


class ProfileHomeTestCase(BaseTestCase):
    url_name = 'profile-home'

    def test_profile_home_unknown(self):
        resp = self.client.post(
            self.reverse(self.url_name, kwargs={'username': 'unknown'}))
        self.assert401(resp)


class ProfileLinkTestCase(BaseTestCase):
    url_name = 'profile-link'

    def test_profile_link_unknown(self):
        resp = self.client.patch(
            self.reverse(self.url_name, kwargs={'username': 'unknown'}))
        self.assert401(resp)


class ProfileListenTestCase(BaseTestCase):
    url_name = 'profile-listen'

    def test_profile_listen_unknown(self):
        resp = self.client.patch(
            self.reverse(self.url_name, kwargs={'username': 'unknown'}))
        self.assert401(resp)


class ProfileListenersTestCase(BaseTestCase):
    url_name = 'profile-listeners'

    def test_profile_listeners_unknown(self):
        resp = self.client.get(
            self.reverse(self.url_name, kwargs={'username': 'unknown'}))
        self.assert404(resp)


class ProfileListeningTestCase(BaseTestCase):
    url_name = 'profile-listening'

    def test_profile_listening_unknown(self):
        resp = self.client.get(
            self.reverse(self.url_name, kwargs={'username': 'unknown'}))
        self.assert404(resp)


class ProfileInterestTestCase(BaseTestCase):
    url_name = 'profile-interests'

    def test_profile_interest_unknown(self):
        resp = self.client.get(
            self.reverse(self.url_name, kwargs={'username': 'unknown'}))
        self.assert404(resp)
