# -*- coding: utf-8 -*-
from django.contrib.auth import get_user_model

from django_dynamic_fixture import G, N

from common.constants import USER_TYPE_PAGE
from shoutit.models import Page, PageCategory
from tests.base import BaseTestCase


class BasePageTestCase(BaseTestCase):
    @classmethod
    def create_page(cls):
        cls.user = cls.create_user()
        cls.pageuser = N(
            get_user_model(),
            type=USER_TYPE_PAGE,
            username='pageuser',
            first_name='Paige',
            is_test=True,
            is_active=True,
            is_activated=True,
            email='page@example.com',
        )
        cls.pagecategory = PageCategory.objects.get(slug='local-business')
        cls.pageuser.page_fields = {
            'name': 'New Page',
            'creator': cls.user,
            'category': cls.pagecategory,
            'country': 'AE',
            'is_published': True,
            'is_verified': True,
        }
        cls.pageuser.set_password(cls.default_password)
        cls.pageuser.save()

    def get_page_url(self):
        return self.reverse(getattr(self, 'url_name'), kwargs={'username': self.pageuser.username})


class PageListTestCase(BasePageTestCase):
    url_name = 'page-list'

    @classmethod
    def setUpTestData(cls):
        cls.create_page()

        cls.pageuser2 = N(
            get_user_model(),
            type=USER_TYPE_PAGE,
            username='pageuser2',
            first_name='Paul',
            is_active=True,
            is_activated=True,
        )
        cls.pageuser2.page_fields = {
            'name': 'Totally different page',
            'creator': cls.pageuser2,
            'category': cls.pagecategory,
            'country': 'DE',
            'is_published': True,
            'is_verified': True,
        }
        cls.pageuser2.save()

    def test_noauth_nodata(self):
        resp = self.client.post(self.reverse(self.url_name))
        self.assert401(resp)

    def test_create_page(self):
        self.login(self.user)
        data = {
            'page_name': 'Super New Page',
            'page_category': {
                'slug': 'local-business',
            }
        }
        page_count_pre = Page.objects.count()
        resp = self.client.post(self.reverse(self.url_name), data)
        self.assert201(resp)
        self.assertEqual(
            Page.objects.count(),
            page_count_pre + 1,
            msg='After the post there should be one more page in the database.'
        )

    def test_list_page(self):
        resp = self.client.get(self.reverse(self.url_name))
        self.assert200(resp)
        self.assertEqual(
            len(self.decode_json(resp)['results']), 2,
            msg='There should be two pages in the results.'
        )

        data = {
            'country': 'AE'
        }
        resp = self.client.get(self.reverse(self.url_name), data)
        self.assert200(resp)
        self.assertEqual(
            len(self.decode_json(resp)['results']), 1,
            msg='There should be one page in the results.'
        )


class PageCategoriesTestCase(BaseTestCase):
    url_name = 'page-categories'

    def test_list_categories(self):
        resp = self.client.get(self.reverse(self.url_name))
        category_count = PageCategory.objects.root_nodes().count()
        self.assert200(resp)
        self.assertEqual(
            len(self.decode_json(resp)), category_count,
            msg='There should be {0} categories in the results. {1}'.format(
                category_count, self.decode_json(resp)
            )
        )


class PageAdminAddRemoveTestCase(BasePageTestCase):
    url_name = 'page-admin'

    @classmethod
    def setUpTestData(cls):
        cls.user2 = cls.create_user(
            username='user2',
            first_name='Two',
        )
        cls.create_page()

    def test_unauth_nodata(self):
        resp = self.client.post(self.get_page_url())
        self.assert401(resp)

    def test_add_delete_admin(self):
        self.login(self.user)
        data = {
            'profile': {
                'id': self.user2.id
            }
        }
        resp = self.client.post(self.get_page_url(), data)
        self.assert200(resp)
        self.assertIn(
            self.user2,
            [pa.admin for pa in self.pageuser.page.pageadmin_set.all()],
            msg='User 2 should now be one of the page admins.'
        )

        resp = self.client.delete(self.get_page_url(), data)
        self.assert200(resp)
        self.assertNotIn(
            self.user2,
            [pa.admin for pa in self.pageuser.page.pageadmin_set.all()],
            msg='User 2 should no longer be one of the page admins.'
        )


class PageAdminsListTestCase(BasePageTestCase):
    url_name = 'page-admins'

    @classmethod
    def setUpTestData(cls):
        cls.create_page()

    def test_list(self):
        resp = self.client.get(self.get_page_url())
        self.assert200(resp)
        self.assertEqual(
            len(self.decode_json(resp)['results']),
            1,
            msg='The results should contain one admin.'
        )


class PageBusinessVerificationTestCase(BasePageTestCase):
    url_name = 'page-verification'

    @classmethod
    def setUpTestData(cls):
        cls.create_page()

    def test_noauth_nodata(self):
        resp = self.client.post(self.get_page_url())
        self.assert401(resp)

        self.login(self.pageuser)
        resp = self.client.post(self.get_page_url(), {
            "business_name": "Super Plumbing Bros",
            "business_email": "sb@example.com",
            "contact_person": "Mario Mario",
            "contact_number": "+491234567890",
            "images": []
        })
        self.assert200(resp)
        self.client.logout()

        # TODO should this really be possible? You could read out business information of all pages via public API like this.
        resp = self.client.get(self.get_page_url())
        self.assert200(resp)
        self.assertEqual(
            self.decode_json(resp).get('status', ''),
            'Waiting',
            msg='Calling the view with GET, it should return the status of the verification.',
        )

    def test_verification(self):
        self.login(self.user)

        resp = self.client.get(self.get_page_url())
        self.assert200(resp)
        self.assertEqual(
            self.decode_json(resp).get('status', ''),
            'Not submitted',
            msg='Calling the view with GET, it should return the status of the verification.',
        )

        data = {
            "business_name": "Super Plumbing Bros",
            "business_email": "sb@example.com",
            "contact_person": "Mario Mario",
            "contact_number": "+491234567890",
            "images": []
        }

        resp = self.client.post(self.get_page_url(), data)
        self.assert200(resp)
        self.assertEqual(
            data['business_name'],
            self.decode_json(resp).get('business_name', ''),
            msg='The response should include the business name',
        )
        self.assertEqual(
            self.decode_json(resp).get('status', ''),
            'Waiting',
            msg='The response should include the status "Waiting".',
        )

        resp = self.client.get(self.get_page_url())
        self.assert200(resp)
        self.assertEqual(
            self.decode_json(resp).get('status', ''),
            'Waiting',
            msg='Calling the view with GET, it should return the status of the verification.',
        )
