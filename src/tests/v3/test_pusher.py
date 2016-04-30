# -*- coding: utf-8 -*-
from unittest import skip

from tests.base import BaseTestCase


class PusherAuthTestCase(BaseTestCase):
    url_name = 'pusher-auth'

    def test_pusher_auth_noauth(self):
        resp = self.client.post(self.reverse(self.url_name))
        self.assert401(resp)


class PusherWebhookTestCase(BaseTestCase):
    url_name = 'pusher-webhook'

    @skip("TODO: raises TypeError")
    def test_pusher_webhook_noauth(self):
        resp = self.client.post(self.reverse(self.url_name))
        self.assert401(resp)
