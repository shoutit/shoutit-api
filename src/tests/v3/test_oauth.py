# -*- coding: utf-8 -*-
from tests.base import BaseTestCase


class AccessTokenTestCase(BaseTestCase):
    url_name = 'access_token'

    def test_access_token_nodata(self):
        resp = self.client.post(self.reverse(self.url_name))
        self.assert400(resp)
