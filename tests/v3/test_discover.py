# -*- coding: utf-8 -*-
from tests.base import BaseTestCase


class DiscoverListTestCase(BaseTestCase):
    url_name = 'discover-list'

    def test_discover_list(self):
        resp = self.client.get(self.reverse(self.url_name))
        self.assert200(resp)


class DiscoverDetailTestCase(BaseTestCase):
    url_name = 'discover-detail'

    def test_discover_unknown(self):
        resp = self.client.get(self.reverse(self.url_name, kwargs={'pk': 1}))
        self.assert404(resp)
