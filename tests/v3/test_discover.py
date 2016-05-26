# -*- coding: utf-8 -*-
import json

from django_dynamic_fixture import G
from shoutit.models import DiscoverItem
from tests.base import BaseTestCase


class DiscoverTestCase(BaseTestCase):
    url_list = 'discover-list'
    url_detail = 'discover-detail'

    @classmethod
    def setUpTestData(cls):
        mptt_fields = ['tree', 'tree_id', 'lft', 'rght', 'level', ]
        cls.d1 = G(DiscoverItem, position=0, ignore_fields=mptt_fields)
        cls.d2 = G(DiscoverItem, position=1, parent=cls.d1,
                   ignore_fields=mptt_fields)
        cls.d3 = G(DiscoverItem, position=2, parent=cls.d2,
                   ignore_fields=mptt_fields)
        cls.d4 = G(DiscoverItem, position=0, ignore_fields=mptt_fields)

    def test_discover_list(self):
        resp = self.client.get(self.reverse(self.url_list))
        self.assert200(resp)
        self.assert_ids_equal(json.loads(resp.content)['results'],
                              [self.d1, self.d4])

    def test_discover_detail_with_children(self):
        resp = self.client.get(
            self.reverse(self.url_detail, kwargs={'pk': self.d1.pk}))
        self.assert200(resp)
        data = json.loads(resp.content)
        self.assertEqual(data['id'], self.d1.pk)
        self.assert_ids_equal(data['parents'], [])
        self.assert_ids_equal(data['children'], [self.d2])

    def test_discover_detail_with_parents(self):
        resp = self.client.get(
            self.reverse(self.url_detail, kwargs={'pk': self.d3.pk}))
        self.assert200(resp)
        data = json.loads(resp.content)
        self.assertEqual(data['id'], self.d3.pk)
        self.assert_ids_equal(data['parents'], [self.d1, self.d2])
        self.assert_ids_equal(data['children'], [])

    def test_discover_detail_with_children_parents(self):
        resp = self.client.get(
            self.reverse(self.url_detail, kwargs={'pk': self.d2.pk}))
        self.assert200(resp)
        data = json.loads(resp.content)
        self.assertEqual(data['id'], self.d2.pk)
        self.assert_ids_equal(data['parents'], [self.d1])
        self.assert_ids_equal(data['children'], [self.d3])

    def test_discover_detail_no_childer_no_parents(self):
        resp = self.client.get(
            self.reverse(self.url_detail, kwargs={'pk': self.d4.pk}))
        self.assert200(resp)
        data = json.loads(resp.content)
        self.assertEqual(data['id'], self.d4.pk)
        self.assert_ids_equal(data['parents'], [])
        self.assert_ids_equal(data['children'], [])

    def test_discover_unknown(self):
        resp = self.client.get(self.reverse(self.url_detail, kwargs={'pk': 0}))
        self.assert404(resp)
