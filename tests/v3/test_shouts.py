# -*- coding: utf-8 -*-
from unittest import skip

from tests.base import BaseTestCase


class ShoutListTestCase(BaseTestCase):
    url_name = 'shout-list'

    @skip("TODO: raises TypeError")
    def test_shout_list_unauth(self):
        resp = self.client.get(self.reverse(self.url_name))
        self.assert200(resp)


class ShoutDetailTestCase(BaseTestCase):
    url_name = 'shout-detail'

    def test_shout_detail_unknown(self):
        resp = self.client.get(self.reverse(self.url_name, kwargs={'id': 1}))
        self.assert400(resp)


class ShoutCallTestCase(BaseTestCase):
    url_name = 'shout-call'

    def test_shout_call_unauth_unknown(self):
        resp = self.client.get(self.reverse(self.url_name, kwargs={'id': 1}))
        self.assert401(resp)


class ShoutRelatedTestCase(BaseTestCase):
    url_name = 'shout-related'

    def test_shout_related_unauth_unknown(self):
        resp = self.client.get(self.reverse(self.url_name, kwargs={'id': 1}))
        self.assert400(resp)


class ShoutReplyTestCase(BaseTestCase):
    url_name = 'shout-reply'

    def test_shout_reply_unauth_unknown(self):
        resp = self.client.post(self.reverse(self.url_name, kwargs={'id': 1}))
        self.assert401(resp)


class ShoutAutocompleteTestCase(BaseTestCase):
    url_name = 'shout-autocomplete'

    def test_shout_autocomplete(self):
        resp = self.client.get(self.reverse(self.url_name))
        self.assert400(resp)


class ShoutCategoriesTestCase(BaseTestCase):
    url_name = 'shout-categories'

    def test_shout_categories(self):
        resp = self.client.get(self.reverse(self.url_name))
        self.assert200(resp)


class ShoutSortTypesTestCase(BaseTestCase):
    url_name = 'shout-sort-types'

    def test_shout_sort_types(self):
        resp = self.client.get(self.reverse(self.url_name))
        self.assert200(resp)
