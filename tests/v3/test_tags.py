# -*- coding: utf-8 -*-
from tests.base import BaseTestCase


class TagListTestCase(BaseTestCase):
    url_name = 'tag-list'

    def test_tag_list(self):
        resp = self.client.get(self.reverse(self.url_name))
        self.assert200(resp)


class TagDetailTestCase(BaseTestCase):
    url_name = 'tag-detail'

    def test_tag_detail_unknown(self):
        resp = self.client.get(
            self.reverse(self.url_name, kwargs={'name': 'unknown'}))
        self.assert404(resp)


class TagListenTestCase(BaseTestCase):
    url_name = 'tag-listen'

    def test_tag_listen_unknown_unauth(self):
        resp = self.client.post(
            self.reverse(self.url_name, kwargs={'name': 'unknown'}))
        self.assert401(resp)


class TagListenersTestCase(BaseTestCase):
    url_name = 'tag-listeners'

    def test_tag_listeners_unknown_unauth(self):
        resp = self.client.get(
            self.reverse(self.url_name, kwargs={'name': 'unknown'}))
        self.assert404(resp)


class TagRelatedTestCase(BaseTestCase):
    url_name = 'tag-related'

    def test_tag_related_unknown_unauth(self):
        resp = self.client.get(
            self.reverse(self.url_name, kwargs={'name': 'unknown'}))
        self.assert404(resp)


class TagBatchListenTestCase(BaseTestCase):
    url_name = 'tag-batch-listen'

    def test_tag_batch_listen_unauth(self):
        resp = self.client.post(
            self.reverse(self.url_name))
        self.assert401(resp)
