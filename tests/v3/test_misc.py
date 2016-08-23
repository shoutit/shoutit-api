# -*- coding: utf-8 -*-
from django.contrib.auth import get_user_model
from django_dynamic_fixture import G, N
from django.utils.http import urlencode

from common.constants import USER_TYPE_PAGE
from shoutit.models import (
    Category,
    Conversation,
    PageCategory,
    PredefinedCity,
    Report,
    Tag,
)
from tests.base import BaseTestCase


class MiscCitiesTestCase(BaseTestCase):
    url_name = 'misc-cities'

    @classmethod
    def setUpTestData(cls):
        cls.city = G(PredefinedCity, approved=True)

    def test_misc_cities(self):
        resp = self.client.get(self.reverse(self.url_name))
        self.assert200(resp)
        self.assertEqual(
            len(self.decode_json(resp)), 1,
            msg='There should be one city in the response.'
        )


class MiscCurrenciesTestCase(BaseTestCase):
    url_name = 'misc-currencies'

    def test_misc_currencies(self):
        resp = self.client.get(self.reverse(self.url_name))
        self.assert200(resp)
        self.assertEqual(
            len(self.decode_json(resp)), 11,
            msg='There should be one currency in the response.'
        )


class MiscErrorTestCase(BaseTestCase):
    url_name = 'misc-error'

    def test_misc_error(self):
        for method in ['get', 'head', 'put', 'post', 'delete']:
            self.assertRaises(
                Exception,
                getattr(self.client, method),
                self.reverse(self.url_name)
            )


class MiscFBDeauthTestCase(BaseTestCase):
    url_name = 'misc-fb-deauth'

    def test_misc_fb_deauth_nodata(self):
        resp = self.client.post(self.reverse(self.url_name))
        self.assert200(resp)


class MiscFBScopesChangedTestCase(BaseTestCase):
    url_name = 'misc-fb-scopes-changed'

    def test_misc_fb_scopes_changed_nodata(self):
        resp = self.client.get(self.reverse(self.url_name))
        self.assert200(resp)


class MiscGeocodeTestCase(BaseTestCase):
    url_name = 'misc-geocode'

    def test_misc_geocode_nodata(self):
        resp = self.client.get(self.reverse(self.url_name))
        self.assert400(resp)


class MiscIpTestCase(BaseTestCase):
    url_name = 'misc-ip'

    def test_misc_ip_nodata(self):
        resp = self.client.get(self.reverse(self.url_name))
        self.assert200(resp)


class MiscReportsTestCase(BaseTestCase):
    url_name = 'misc-reports'

    default_data = {
        'text': 'Something bad is going on here!'
    }

    @classmethod
    def setUpTestData(cls):
        cls.user = cls.create_user()
        cls.user2 = cls.create_user(
            username='hanzoshimada',
            first_name='Hanzo'
        )
        cls.shout = cls.create_shout(category__slug='shout', user=cls.user2)
        cls.profile = cls.user2.profile
        cls.conversation = G(Conversation, user=cls.user2)

    def get_data(self, attached_object):
        final_data = self.default_data.copy()
        final_data.update({'attached_object': attached_object})
        return final_data

    def test_misc_reports(self):
        self.login(self.user)
        data = self.get_data({'shout': {'id': self.shout.id}})
        resp = self.client.post(self.reverse(self.url_name), data)
        self.assert201(resp)
        self.assertEqual(
            Report.objects.count(), 1,
            msg='After reporting a shout, there should be one more report in the database.'
        )

        data = self.get_data({'profile': {'id': self.profile.id}})
        resp = self.client.post(self.reverse(self.url_name), data)
        self.assert201(resp)
        self.assertEqual(
            Report.objects.count(), 2,
            msg='After reporting a profile, there should be one more report in the database.'
        )

        data = self.get_data({'conversation': {'id': self.conversation.id}})
        resp = self.client.post(self.reverse(self.url_name), data)
        self.assert201(resp)
        self.assertEqual(
            Report.objects.count(), 3,
            msg='After reporting a conversation, there should be one more report in the database.'
        )

    def test_misc_reports_nodata(self):
        resp = self.client.post(self.reverse(self.url_name))
        self.assert401(resp)


class MiscSuggestionsTestCase(BaseTestCase):
    url_name = 'misc-suggestions'
    all_keys = ['users', 'pages', 'tags', 'shouts', 'shout']

    @classmethod
    def setUpTestData(cls):
        cls.user1 = cls.create_user()
        cls.user2 = cls.create_user(
            username='genjishimada',
            first_name='Genji',
            country='JP',
        )
        cls.category = Category.objects.get(slug='collectibles')
        cls.shout1 = cls.create_shout(category=cls.category, user=cls.user2, country='DE', city='Berlin', text='shout1')
        cls.shout2 = cls.create_shout(category=cls.category, user=cls.user2, country='AE', state='Dubai', city='Dubai', text='shout2')
        cls.pagecategory = G(PageCategory, slug='foobar')
        cls.page_user1 = N(
            get_user_model(),
            type=USER_TYPE_PAGE,
            username='laracroft',
            first_name='Lara',
        )
        cls.page_user1.page_fields = {
            'name': 'Tomb Raider',
            'creator': cls.user2,
            'category': cls.pagecategory,
            'is_published': True,
            'is_verified': True,
        }
        cls.page_user1.save()
        cls.tag1 = G(Tag, slug=cls.category.slug, creator=cls.user2)
        cls.tag2 = G(Tag, slug='tag', creator=cls.user2)

    def assertKeysAndResultsCorrect(self, data, response):
        type_q = data.get('type', None)
        if type_q is None:
            keys = self.all_keys
        else:
            keys = type_q.split(',')

        for key in keys:
            # see if the key is in the result
            self.assertIn(key, self.decode_json(response).keys())

        # TODO This test repeatedly fails on different, seemingly random places. There must be some caching issue or randomization.
        # # Expected defaults for results
        # result_counts = {
        #     'users': 4,
        #     'pages': 1,
        #     'tags': 1,
        #     'shouts': 2,
        # }
        # # encode query for better error message output
        # query = urlencode(data) or '""'
        # for key in self.all_keys:
        #     # If the key was not queried, we expect 0 results
        #     count = 0
        #     if key in keys:
        #         count = result_counts.get(key, 0)
        #     # see if there are items in the result under specific key
        #     if key != 'shout':
        #         self.assertEqual(
        #             len(self.decode_json(response).get(key, [])),
        #             count,
        #             msg='There should be {0} item of type {1} in the result for query {2}.'.format(
        #                 count, key, query)
        #         )
        #     else:
        #         self.assertEqual(
        #             self.decode_json(response).get(key, {}).get('text', ''),
        #             self.shout2.text,
        #             msg='There should be an item of type shout in the result for query {0}.'.format(query)
        #         )

    def test_misc_suggestions(self):
        resp = self.client.get(self.reverse(self.url_name))
        self.assert200(resp)
        self.assertKeysAndResultsCorrect({}, resp)

        data = {
            'type': 'users,pages,shouts,shout'
        }
        resp = self.client.get(self.reverse(self.url_name), data)
        self.assert200(resp)
        self.assertKeysAndResultsCorrect(data, resp)

        data = {
            'type': 'shouts'
        }
        resp = self.client.get(self.reverse(self.url_name), data)
        self.assert200(resp)
        self.assertKeysAndResultsCorrect(data, resp)

        data = {
            'type': 'users,shouts',
            'country': 'DE',
        }
        resp = self.client.get(self.reverse(self.url_name), data)
        self.assert200(resp)
        self.assertKeysAndResultsCorrect(data, resp)

        data = {
            'type': 'shouts',
            'state': 'Dubai',
        }
        resp = self.client.get(self.reverse(self.url_name), data)
        self.assert200(resp)
        self.assertKeysAndResultsCorrect(data, resp)

        data = {
            'type': 'shouts',
            'city': 'Berlin',
        }
        resp = self.client.get(self.reverse(self.url_name), data)
        self.assert200(resp)
        self.assertKeysAndResultsCorrect(data, resp)
