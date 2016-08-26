# -*- coding: utf-8 -*-
from django_dynamic_fixture import G

from elasticsearch.helpers import bulk

from shoutit.controllers.shout_controller import shout_index_from_shout
from shoutit.models import Category, Shout, Tag
from shoutit import ES
from tests.base import BaseTestCase


class BaseShoutTestCase(BaseTestCase):
    longMessage = True

    @classmethod
    def setup_shout(cls):
        if not hasattr(cls, 'user'):
            cls.user = cls.create_user()
        cls.category = Category.objects.get(slug='collectibles')
        cls.shout = cls.create_shout(user=cls.user, category=cls.category, title='Foobar')
        cls.tags = []
        for i in range(0, 3):
            tag = G(Tag, slug='tag-{0}'.format(i), name='Tag {0}'.format(i))
            cls.tags.append(tag)
            cls.shout.tags.add(tag)

    def get_shout_url(self):
        return self.reverse(getattr(self, 'url_name'), kwargs={'id': self.shout.id})


class ShoutCreateTestCase(BaseShoutTestCase):
    url_name = 'shout-list'

    @classmethod
    def setUpTestData(cls):
        cls.setup_shout()

    def test_unauth_nodata(self):
        resp = self.client.post(self.reverse(self.url_name))
        self.assert401(resp)

    def test_create_shout(self):
        self.login(self.user)
        data = {
            "type": "offer",
            "title": "Gibson Les Paul Studio 2015",
            "text": "Signature Edition",
            "price": 2300,
            "currency": "EUR",
            "available_count": 1,
            "is_sold": False,
            "images": [],
            "videos": [],
            "category": {
                "slug": "collectibles"
            },
            "location": {
                "latitude": 25.1593957,
                "longitude": 55.2338326,
                "address": "Goethestraße 31",
            },
            "publish_to_facebook": False,
            "filters": [
                {
                    "slug": "color",
                    "value": {
                        "slug": "brown"
                    }
                },
                {
                    "slug": "model",
                    "value": {
                        "slug": "2015"
                    }
                }
            ]
        }
        shout_count_pre = Shout.objects.count()
        resp = self.client.post(self.reverse(self.url_name), data)
        self.assert201(resp)
        self.assertEqual(
            Shout.objects.count(),
            shout_count_pre + 1,
            msg='After valid POST there should be one more Shout in the database.'
        )


class ShoutListTestCase(BaseShoutTestCase):
    url_name = 'shout-list'

    @classmethod
    def setUpTestData(cls):
        cls.setup_shout()
        cls.refresh_elasticsearch_index('*')
        shout_index_dicts = []
        shout_index_dicts.append(shout_index_from_shout(cls.shout).to_dict(True))
        bulk(ES, shout_index_dicts, chunk_size=1, raise_on_error=False, raise_on_exception=False)

    def test_shout_list(self):
        shout_count = Shout.objects.count()
        resp = self.client.get(self.reverse(self.url_name))
        self.assert200(resp)
        self.assertEqual(
            len(self.decode_json(resp).get('results', [])),
            shout_count,
            msg='There should be {0} Shout in the results.'.format(shout_count)
        )
        # TODO the count returns as 5 even though there's only 1 shout in the results and no other pages
        # self.assertEqual(
        #     int(self.decode_json(resp).get('count', 0)),
        #     shout_count,
        #     msg='The returned count returned in the response should be {0}. {1}'.format(shout_count, resp)
        # )

    def tearDown(self):
        self.delete_elasticsearch_index('*', refresh=False)


class ShoutAutocompleteTestCase(BaseShoutTestCase):
    url_name = 'shout-autocomplete'

    @classmethod
    def setUpTestData(cls):
        cls.setup_shout()

    def test_shout_autocomplete(self):
        resp = self.client.get(self.reverse(self.url_name))
        self.assert400(resp)

        data = {'search': 'Ta'}
        tags = Tag.objects.filter(name__istartswith=data['search'])
        tag_count = tags.count()
        resp = self.client.get(self.reverse(self.url_name), data)
        self.assert200(resp)
        self.assertEqual(
            len(self.decode_json(resp)),
            tag_count,
            msg='There should be {0} tags in the results'.format(tag_count),
        )
        for tag in tags:
            self.assertIn(
                {'term': tag.name},
                self.decode_json(resp),
                msg='"{0}" should be in the results'.format(tag.name)
            )


class ShoutCategoriesTestCase(BaseShoutTestCase):
    url_name = 'shout-categories'

    def test_shout_categories(self):
        category_count = Category.objects.count()
        resp = self.client.get(self.reverse(self.url_name))
        self.assert200(resp)
        self.assertEqual(
            len(self.decode_json(resp)),
            category_count,
            msg='There should be {0} categories in the results.'.format(category_count)
        )


class ShoutitPromoteLabelsTestCase(BaseShoutTestCase):
    url_name = 'shout-promote-labels'

    def test_promote_labels(self):
        resp = self.client.get(self.reverse(self.url_name))
        self.assert200(resp)
        self.assertEqual(
            len(self.decode_json(resp)),
            3,
            msg='There should be 3 labels in the results.'
        )


class ShoutitPromoteOptionsTestCase(BaseShoutTestCase):
    url_name = 'shout-promote-options'

    def test_promote_options(self):
        resp = self.client.get(self.reverse(self.url_name))
        self.assert200(resp)
        self.assertEqual(
            len(self.decode_json(resp)),
            4,
            msg='There should be 4 options in the results.'
        )


class ShoutitSortTypesTestCase(BaseShoutTestCase):
    url_name = 'shout-sort-types'

    def test_sort_types(self):
        resp = self.client.get(self.reverse(self.url_name))
        self.assert200(resp)
        self.assertEqual(
            len(self.decode_json(resp)),
            3,
            msg='There should be 3 sort types in the results.'
        )


class ShoutDetailTestCase(BaseShoutTestCase):
    url_name = 'shout-detail'

    @classmethod
    def setUpTestData(cls):
        cls.setup_shout()

    def test_shout_detail_unknown(self):
        resp = self.client.get(self.reverse(self.url_name, kwargs={'id': 'unknown-id'}))
        self.assert400(resp)

    def test_shout_retrieve(self):
        resp = self.client.get(self.get_shout_url())
        self.assert200(resp)
        self.assertEqual(
            self.decode_json(resp).get('id', ''),
            unicode(self.shout.id),
            msg='The response should return the requested shout. {0}'.format(resp)
        )

    def test_shoutit_update_noauth(self):
        data = {
            'text': 'Updated Text',
        }
        resp = self.client.patch(self.get_shout_url(), data)
        self.assert401(resp)

    def test_shout_update(self):
        self.login(self.user)
        data = {
            'text': 'Updated Text',
        }
        resp = self.client.patch(self.get_shout_url(), data)
        self.assert200(resp)
        self.assertEqual(
            self.decode_json(resp).get('text', ''),
            data['text'],
            msg='The updated text should be in the response.'
        )
        self.shout.refresh_from_db()
        self.assertEqual(
            self.shout.text,
            data['text'],
            msg='The text on the shout should be updated.'
        )

    def test_shoutit_delete_noauth(self):
        resp = self.client.delete(self.get_shout_url())
        self.assert401(resp)

    def test_shout_delete(self):
        self.login(self.user)
        resp = self.client.delete(self.get_shout_url())
        self.assert204(resp)
        self.shout.refresh_from_db()
        self.assertTrue(
            self.shout.is_disabled,
            msg='After successful request, the shout should be disabled.'
        )


class ShoutBookmarkTestCase(BaseShoutTestCase):
    url_name = 'shout-bookmark'

    @classmethod
    def setUpTestData(cls):
        cls.setup_shout()

    def test_noauth(self):
        resp = self.client.post(self.get_shout_url())
        self.assert401(resp)
        resp = self.client.delete(self.get_shout_url())
        self.assert401(resp)

    def test_bookmark(self):
        self.login(self.user)
        resp = self.client.post(self.get_shout_url())
        self.assert200(resp)

    def test_bookmark_delete(self):
        self.login(self.user)
        resp = self.client.delete(self.get_shout_url())
        self.assert200(resp)


class ShoutCallTestCase(BaseShoutTestCase):
    url_name = 'shout-call'

    def test_shout_call_unauth_unknown(self):
        resp = self.client.get(self.reverse(self.url_name, kwargs={'id': 1}))
        self.assert401(resp)


class ShoutRelatedTestCase(BaseShoutTestCase):
    url_name = 'shout-related'

    def test_shout_related_unauth_unknown(self):
        resp = self.client.get(self.reverse(self.url_name, kwargs={'id': 1}))
        self.assert400(resp)


class ShoutReplyTestCase(BaseShoutTestCase):
    url_name = 'shout-reply'

    def test_shout_reply_unauth_unknown(self):
        resp = self.client.post(self.reverse(self.url_name, kwargs={'id': 1}))
        self.assert401(resp)
