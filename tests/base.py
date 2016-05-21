# -*- coding: utf-8 -*-
from rest_framework.test import APITestCase
from django.core.urlresolvers import reverse


class BaseTestCase(APITestCase):
    url_namespace = 'v3'

    def reverse(cls, url_name, *args, **kwargs):
        return reverse(cls.url_namespace + ':' + url_name, *args, **kwargs)

    def assertIdsEqual(self, dict_iter, objects_iter, order=False):
        id_list_1 = [str(o['id']) for o in dict_iter]
        id_list_2 = [str(o.id) for o in objects_iter]
        self.assertEqual(len(id_list_1), len(id_list_2))
        if order:
            self.assertEqual(id_list_1, id_list_2)
        else:
            self.assertEqual(set(id_list_1), set(id_list_2))

    def assert200(self, response):
        self.assertEqual(response.status_code, 200)

    def assert400(self, response):
        self.assertEqual(response.status_code, 400)

    def assert401(self, response):
        self.assertEqual(response.status_code, 401)

    def assert404(self, response):
        self.assertEqual(response.status_code, 404)
