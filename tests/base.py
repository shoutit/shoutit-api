# -*- coding: utf-8 -*-
import json
from datetime import timedelta

from rest_framework.test import APITestCase
from django.core.urlresolvers import reverse
from django.contrib.auth import get_user_model
from django_dynamic_fixture import N
from django.utils import timezone
from mock import MagicMock
from push_notifications import apns

from shoutit_pusher import utils as pusher_utils
from shoutit import utils as shoutit_utils


# mock pusher
mocked_pusher = MagicMock()
mocked_pusher.authenticate = MagicMock(return_value={'pusher': 'success'})
mocked_pusher.validate_webhook = MagicMock()
unmocked_pusher, pusher_utils.pusher = pusher_utils.pusher, mocked_pusher

# mock push
apns.apns_send_message = mocked_apns_send_message = MagicMock()
apns.apns_send_bulk_message = mocked_apns_send_bulk_message = MagicMock()
apns.apns_fetch_inactive_ids = mocked_apns_fetch_inactive_ids = MagicMock()

# mock Mixpanel
shoutit_utils.shoutit_mp = MagicMock()


class BaseTestCase(APITestCase):
    url_namespace = 'v3'

    def assert200(self, response):
        self.assertEqual(response.status_code, 200)

    def assert201(self, response):
        self.assertEqual(response.status_code, 201)

    def assert202(self, response):
        self.assertEqual(response.status_code, 202)

    def assert204(self, response):
        self.assertEqual(response.status_code, 204)

    def assert400(self, response):
        self.assertEqual(response.status_code, 400)

    def assert401(self, response):
        self.assertEqual(response.status_code, 401)

    def assert404(self, response):
        self.assertEqual(response.status_code, 404)

    def assert403(self, response):
        self.assertEqual(response.status_code, 403)

    def reverse(cls, url_name, *args, **kwargs):
        return reverse(cls.url_namespace + ':' + url_name, *args, **kwargs)

    def assert_ids_equal(self, dict_iter, objects_iter, order=False):
        id_list_1 = [str(o['id']) for o in dict_iter]
        id_list_2 = [str(o.id) for o in objects_iter]
        self.assertEqual(len(id_list_1), len(id_list_2))
        if order:
            self.assertEqual(id_list_1, id_list_2)
        else:
            self.assertEqual(set(id_list_1), set(id_list_2))

    def assert_ios_badge_set(self, mocked_apns_bulk, device_ids, **kwargs):
        self.assertTrue(mocked_apns_bulk.called)
        _, call_kwargs = self.get_mock_call_args_kwargs(mocked_apns_bulk)
        self.assertEqual(call_kwargs['registration_ids'], device_ids)
        for k, v in kwargs.items():
            self.assertEqual(call_kwargs[k], v)

    def assert_pusher_event(self, mocked_trigger, event_name,
                            channel_name=None,
                            attached_object_partial_dict=None,
                            call_count=0):
        self.assertTrue(mocked_trigger.called)
        args, _ = self.get_mock_call_args_kwargs(mocked_trigger, call_count)
        self.assertEqual(args[1], event_name, "event_name")
        if channel_name is not None:
            self.assertEqual(args[0], channel_name, "channel_name")
        if attached_object_partial_dict is not None:
            attached_object_dict = args[2]
            for k, v in attached_object_partial_dict.items():
                self.assertEqual(attached_object_dict[k], v)

    def decode_json(self, response):
        return json.loads(response.content.decode('utf8'))

    def get_mock_call_args_kwargs(self, mocked_object, call_count=0):
        return (mocked_object.call_args_list[call_count][0],
                mocked_object.call_args_list[call_count][1])

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

    @classmethod
    def dt_before(cls, **kwargs):
        return timezone.now() - timedelta(**kwargs)

    @classmethod
    def update_auto_dt_field(cls, instance, field_name, value):
        """
        To set value for datetime field with auto_now or auto_now_add
        attributes we have to make update.
        Just assigning will not work.
        """
        kwargs = {field_name: value}
        instance.__class__.objects.filter(pk=instance.pk).update(**kwargs)
        # to update value in current instance
        setattr(instance, field_name, value)
