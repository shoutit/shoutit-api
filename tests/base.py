# -*- coding: utf-8 -*-
from rest_framework.test import APITestCase
from django.core.urlresolvers import reverse


class BaseTestCase(APITestCase):
    url_namespace = 'v3'

    def reverse(cls, url_name, *args, **kwargs):
        return reverse(cls.url_namespace + ':' + url_name, *args, **kwargs)

    def assert200(self, response):
        self.assertEqual(response.status_code, 200)

    def assert400(self, response):
        self.assertEqual(response.status_code, 400)

    def assert401(self, response):
        self.assertEqual(response.status_code, 401)

    def assert404(self, response):
        self.assertEqual(response.status_code, 404)
