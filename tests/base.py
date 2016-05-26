# -*- coding: utf-8 -*-
from rest_framework.test import APITestCase
from django.core.urlresolvers import reverse
from django.contrib.auth import get_user_model
from django_dynamic_fixture import N
from mock import MagicMock

from shoutit_pusher import utils


# mock pusher
def mocked_validate_webhook(key, *args, **kwargs):
    if not isinstance(key, basestring):
        raise TypeError('key should be a unicode string')
    return {}

mocked_pusher = MagicMock()
mocked_pusher.authenticate = MagicMock(return_value={'pusher': 'success'})
mocked_pusher.validate_webhook = MagicMock(
    side_effect=mocked_validate_webhook)
unmocked_pusher, utils.pusher = utils.pusher, mocked_pusher


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

    @classmethod
    def create_user(cls, username='ivan', first_name='Ivan', password='123',
                    is_test=True, **kwargs):
        user = N(
            get_user_model(),
            username=username,
            first_name=first_name,
            is_test=is_test,
            **kwargs
        )
        user.set_password(password)
        user.save()
        return user
