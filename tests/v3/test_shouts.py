# -*- coding: utf-8 -*-
from django.utils.timezone import now, timedelta
from django_dynamic_fixture import G, N
from mock import patch

from common.constants import DEFAULT_LOCATION
from shoutit.models import Category, Message, Shout, Tag
from shoutit_credit.models import CreditTransaction, PromoteShouts
from tests.base import BaseTestCase


class BaseShoutTestCase(BaseTestCase):
    longMessage = True

    # Todo (Nour): Use shout_controller.create_shout instead. Creating shouts is complicated and should not be mimicked.
    @classmethod
    def setup_shout(cls):
        if not hasattr(cls, 'user'):
            cls.user = cls.create_user()
        cls.category = Category.objects.get(slug='collectibles')
        cls.shout = cls.create_shout(user=cls.user, category=cls.category, title='Foobar')
        cls.tags = []
        for slug in ['blue', 'old', 'metal']:
            tag = G(Tag, slug=slug, name=slug.capitalize())
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
            "images": [
                "https://shout-image.static.shoutit.com/1506323989994_bed63730-6107-420b-8996-36d0ce3c1c96.jpg"
            ],
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
        cls.delete_elasticsearch_index('*')
        cls.setup_shout()
        cls.refresh_elasticsearch_index('*')

    def test_shout_list(self):
        shout_count = Shout.objects.count()
        resp = self.client.get(self.reverse(self.url_name))
        self.assert200(resp)
        self.assertEqual(
            shout_count,
            len(self.decode_json(resp).get('results', [])),
            msg='There should be {0} Shout in the results.'.format(shout_count)
        )
        self.assertEqual(
            int(self.decode_json(resp).get('count', 0)),
            shout_count,
            msg='The returned count returned in the response should be {0}. {1}'.format(shout_count, resp)
        )


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

        data = {'search': 'T'}
        resp = self.client.get(self.reverse(self.url_name), data)
        self.assert400(resp)


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
            str(self.shout.id),
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

    @classmethod
    def setUpTestData(cls):
        cls.setup_shout()

    def test_shout_call_unauth_unknown(self):
        resp = self.client.get(self.reverse(self.url_name, kwargs={'id': 1}))
        self.assert401(resp)

    def test_mobile(self):
        self.login(self.user)
        resp = self.client.get(self.get_shout_url())
        self.assert400(resp)

        phone = '+49555123456'
        Shout.objects.all().update(mobile=phone)
        resp = self.client.get(self.get_shout_url())
        self.assert200(resp)
        self.assertEqual(
            self.decode_json(resp).get('mobile', ''),
            phone,
            msg="Should have retrieved the shout's phone number."
        )


class ShoutLikeTestCase(BaseShoutTestCase):
    url_name = 'shout-like'

    @classmethod
    def setUpTestData(cls):
        cls.setup_shout()
        cls.user2 = cls.create_user(
            username='user2',
            first_name='User',
        )

    def test_noauth(self):
        resp = self.client.post(self.get_shout_url())
        self.assert401(resp)
        resp = self.client.delete(self.get_shout_url())
        self.assert401(resp)

    def test_like(self):
        self.login(self.user2)
        resp = self.client.post(self.get_shout_url())
        self.assert200(resp)

    def test_like_delete(self):
        self.login(self.user2)
        resp = self.client.delete(self.get_shout_url())
        self.assert200(resp)


class ShoutPromoteTestCase(BaseShoutTestCase):
    url_name = 'shout-promote'

    @classmethod
    def setUpTestData(cls):
        cls.setup_shout()
        cls.credit_rule = PromoteShouts.objects.all()[0]
        cls.credit_transaction = N(CreditTransaction, user=cls.user,
                                   rule=cls.credit_rule, amount=9001)
        cls.credit_transaction.notify = False
        cls.credit_transaction.save()

    def test_unauth(self):
        resp = self.client.patch(self.get_shout_url())
        self.assert401(resp)

    @patch.object(CreditTransaction, 'notify_user')
    def test_promote(self, notify_mock):
        self.login(self.user)
        self.assertTrue(self.user.credit_transactions.all().count())
        data = {
            'option': {
                'id': PromoteShouts.objects.all()[0].id
            }
        }
        resp = self.client.patch(self.get_shout_url(), data)
        self.assert200(resp)
        self.assertEqual(
            self.decode_json(resp).get('success', ''),
            'The shout has been promoted'
        )


class ShoutRelatedTestCase(BaseShoutTestCase):
    url_name = 'shout-related'

    @classmethod
    def setUpTestData(cls):
        cls.delete_elasticsearch_index('*')
        user = cls.create_user()
        category = Category.objects.get(slug='services')
        cls.shout1 = cls.create_shout2(user=user, shout_type=0, title='Pets Service 1', text='', price=None,
                                       currency=None, category=category, location=DEFAULT_LOCATION)
        cls.shout2 = cls.create_shout2(user=user, shout_type=0, title='Pets Service 2', text='', price=None,
                                       currency=None, category=category, location=DEFAULT_LOCATION)
        cls.refresh_elasticsearch_index('*')

    def test_shout_related_auth(self):
        resp = self.client.get(self.reverse(self.url_name, kwargs={'id': self.shout1.id}))
        self.assert200(resp)
        self.assertEqual(
            1,
            len(self.decode_json(resp)['results']),
            msg='There should be one shout in the results. {0}'.format(resp)
        )
        self.assertEqual(
            str(self.shout2.id),
            self.decode_json(resp)['results'][0].get('id'),
            msg='The related shout should be in the results'
        )


class ShoutReplyTestCase(BaseShoutTestCase):
    url_name = 'shout-reply'

    @classmethod
    def setUpTestData(cls):
        cls.setup_shout()
        cls.user2 = cls.create_user(
            username='user2',
            first_name='user',
        )

    def test_shout_reply_unauth_unknown(self):
        resp = self.client.post(self.reverse(self.url_name, kwargs={'id': 1}))
        self.assert401(resp)

    def test_shout_reply(self):
        self.login(self.user2)
        data = {
            'text': 'Shout reply text'
        }
        resp = self.client.post(self.get_shout_url(), data)
        self.assert201(resp)
        self.assertEqual(
            self.decode_json(resp).get('id', ''),
            str(Message.objects.get().id),
            msg='Response should contain the shout id. {0}'.format(resp)
        )

    def test_shout_reply_own_shout(self):
        self.login(self.user)
        data = {
            'text': 'Shout reply text'
        }
        resp = self.client.post(self.get_shout_url(), data)
        self.assert400(resp)

    def test_shout_expired(self):
        self.login(self.user2)
        Shout.objects.all().update(expires_at=now() - timedelta(days=1))
        data = {
            'text': 'Shout reply text'
        }
        resp = self.client.post(self.get_shout_url(), data)
        self.assert404(resp)
