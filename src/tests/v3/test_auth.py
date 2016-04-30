# -*- coding: utf-8 -*-
from tests.base import BaseTestCase


class ChangePasswordTestCase(BaseTestCase):
    url_name = 'shoutit_auth-change-password'

    def test_unauth_no_data(self):
        resp = self.client.post(self.reverse(self.url_name))
        self.assert401(resp)


class ResetPasswordTestCase(BaseTestCase):
    url_name = 'shoutit_auth-reset-password'

    def test_unauth_no_data(self):
        resp = self.client.post(self.reverse(self.url_name))
        self.assert400(resp)


class SetPasswordTestCase(BaseTestCase):
    url_name = 'shoutit_auth-set-password'

    def test_unauth_no_data(self):
        resp = self.client.post(self.reverse(self.url_name))
        self.assert400(resp)


class VerifyEmailTestCase(BaseTestCase):
    url_name = 'shoutit_auth-verify-email'

    def test_resend_unauth_no_data(self):
        resp = self.client.post(self.reverse(self.url_name))
        self.assert401(resp)

    def test_verify_unauth_no_data(self):
        resp = self.client.get(self.reverse(self.url_name))
        self.assert400(resp)
