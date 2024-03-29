# -*- coding: utf-8 -*-
import os
import json
import random
import string
from datetime import timedelta

from django.db.models.query import QuerySet
from rest_framework.test import APITestCase
from django.core.urlresolvers import reverse
from django.contrib.auth import get_user_model
from django_dynamic_fixture import N, G, F
from django.utils import timezone
from mock import MagicMock
from push_notifications import apns, gcm
import responses
import boto3

from shoutit.controllers import mixpanel_controller
from shoutit_pusher import utils as pusher_utils
from shoutit import ES, settings
from shoutit.models.misc import LocationIndex
from shoutit.models.post import ShoutIndex, Post, Shout
from shoutit.models import Profile

# mock pusher
mocked_pusher = MagicMock()
mocked_pusher.authenticate = MagicMock(return_value={'pusher': 'success'})
mocked_pusher.validate_webhook = MagicMock()
unmocked_pusher, pusher_utils.pusher = pusher_utils.pusher, mocked_pusher

# mock push
apns.apns_send_message = mocked_apns_send_message = MagicMock()
apns.apns_send_bulk_message = mocked_apns_send_bulk_message = MagicMock()
apns.apns_fetch_inactive_ids = mocked_apns_fetch_inactive_ids = MagicMock()

gcm.gcm_send_message = mocked_gcm_send_message = MagicMock()
gcm.gcm_send_bulk_message = mocked_gcm_send_bulk_message = MagicMock()

# mock Mixpanel
mixpanel_controller.shoutit_mp = MagicMock()
mixpanel_controller.shoutit_mp_buffered = MagicMock()

# mock s3 boto3
boto3.resource = MagicMock()

# TODO: refactor application code, so shout signal will be applied
#       automatically (currently shout_post_save signal is not called
#       because it is not automatically imported)
#       Following import is present only to apply signals
#       The mocking has to be done first
from shoutit.controllers import shout_controller  # NOQA


class BaseTestCase(APITestCase):
    url_namespace = 'v3'
    default_password = 'test123'
    default_username = 'ivan'
    default_first_name = 'Ivan'
    default_email = 'ivan@example.com'
    IPS = {
        'CHINA': '14.131.255.15',
        'USA': '72.229.28.185',  # New York
    }
    COORDINATES = {
        'USA': {
            'latitude': 40.714057,
            'longitude': -74.006625,
        }
    }
    LOCATIONS = {
        'USA': {
            'address': '267 Canyon of Heroes, New York, NY 10007, USA',
            'city': 'New York',
            'country': 'US',
            'latitude': 40.714057,
            'longitude': -74.006625,
            'postal_code': '10007',
            'state': 'New York'
        }
    }

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

    def assert406(self, response):
        self.assertEqual(response.status_code, 406)

    def assert_ids_equal(self, dict_iter, objects_iter, order=False):
        if not isinstance(dict_iter, (list, QuerySet)):
            dict_iter = [dict_iter]
        if not isinstance(objects_iter, (list, QuerySet)):
            objects_iter = [objects_iter]
        id_list_1 = [str(o['id']) for o in dict_iter]
        id_list_2 = [str(o.id) for o in objects_iter]
        self.assertEqual(len(id_list_1), len(id_list_2))
        if order:
            self.assertEqual(id_list_1, id_list_2)
        else:
            self.assertEqual(set(id_list_1), set(id_list_2))

    def assert_ios_badge_set(self, mocked_apns_bulk, device_ids, call_count=0,
                             **kwargs):
        self.assertTrue(mocked_apns_bulk.called)
        _, call_kwargs = self.get_mock_call_args_kwargs(
            mocked_apns_bulk, call_count)
        self.assertEqual(call_kwargs['registration_ids'], device_ids)
        for k, v in kwargs.items():
            self.assertEqual(call_kwargs[k], v)
        return call_kwargs

    def assert_gcm_sent(self, mocked_gcm_bulk, device_ids, call_count=0,
                        **kwargs):
        self.assertTrue(mocked_gcm_bulk.called)
        _, call_kwargs = self.get_mock_call_args_kwargs(
            mocked_gcm_bulk, call_count)
        self.assertEqual(call_kwargs['registration_ids'], device_ids)
        for k, v in kwargs.items():
            self.assertEqual(call_kwargs[k], v)
        return call_kwargs

    def assert_pusher_event(self, mocked_trigger, event_name,
                            channel_name=None,
                            attached_object_partial_dict=None,
                            call_count=0, try_all=False):
        self.assertTrue(mocked_trigger.called)
        if try_all:
            for i in range(mocked_trigger.call_count):
                args, _ = self.get_mock_call_args_kwargs(mocked_trigger, i)
                if args[1] == event_name:
                    call_count = i
                    break
            else:
                self.assertTrue(False,
                                'No call for Pusher event %s' % event_name)
        args, _ = self.get_mock_call_args_kwargs(mocked_trigger, call_count)
        self.assertEqual(args[1], event_name)
        if channel_name is not None:
            self.assertEqual(args[0], channel_name, "channel_name")
        if attached_object_partial_dict is not None:
            attached_object_dict = args[2]
            for k, v in attached_object_partial_dict.items():
                self.assertEqual(attached_object_dict[k], v)
        return args

    def login(self, user, password=default_password, **kwargs):
        self.client.login(username=user.username, password=password, **kwargs)

    def get_pusher_user_channel_name(self, user_pk):
        return 'presence-%s-p-%s' % (self.url_namespace, user_pk)

    def get_pusher_conversation_channel_name(self, conv_pk):
        return 'presence-%s-c-%s' % (self.url_namespace, conv_pk)

    def decode_json(self, response):
        return json.loads(response.content.decode('utf8'))

    def get_mock_call_args_kwargs(self, mocked_object, call_count=0):
        return (mocked_object.call_args_list[call_count][0],
                mocked_object.call_args_list[call_count][1])

    @classmethod
    def create_shout(cls, **kwargs):
        if 'post_ptr' not in kwargs:
            kwargs['post_ptr'] = G(
                Post,
                user=cls.create_user(username=cls.get_random_string(10))
            )
        if 'category' not in kwargs:
            kwargs['category'] = F()
        if 'user' not in kwargs:
            kwargs['user'] = cls.create_user(
                username=cls.get_random_string(10))
        return G(Shout, **kwargs)

    @classmethod
    def create_shout2(cls, **kwargs):
        return shout_controller.create_shout(**kwargs)

    @classmethod
    def get_video_data(cls, **data):
        data.setdefault('url', 'http://yout.com/v1')
        data.setdefault('thumbnail_url', 'http://s3.com/v1.png')
        data.setdefault('provider', 'youtube')
        data.setdefault('id_on_provider', 'v1')
        data.setdefault('duration', 30)
        return data

    @classmethod
    def get_random_string(cls, length):
        return ''.join(random.choice(
            string.ascii_letters) for i in range(length))

    @classmethod
    def reverse(cls, url_name, *args, **kwargs):
        return reverse(cls.url_namespace + ':' + url_name, *args, **kwargs)

    @classmethod
    def delete_elasticsearch_index(cls, index, reinit=True, refresh=True):
        ES.indices.delete(index=f'{settings.ES_BASE_INDEX}_{index}')
        if reinit:
            LocationIndex.init()
            ShoutIndex.init()
        if refresh:
            cls.refresh_elasticsearch_index(index=index)

    @classmethod
    def refresh_elasticsearch_index(cls, index):
        ES.indices.refresh(index=f'{settings.ES_BASE_INDEX}_{index}')

    @classmethod
    def add_googleapis_geocode_response(cls, json_file_name, status=200, add_path=True):
        if add_path:
            current_dir = os.path.dirname(os.path.realpath(__file__))
            json_file_name = os.path.join(current_dir, 'data', 'googleapis', json_file_name)

        with open(json_file_name) as f:
            responses.add(
                responses.GET,
                'https://maps.googleapis.com/maps/api/geocode/json',
                json=json.load(f),
                status=status)

    @classmethod
    def create_user(cls, username=default_username, first_name=default_first_name,
                    password=default_password, is_test=True, country=None,
                    **kwargs):
        user = N(
            get_user_model(),
            username=username,
            first_name=first_name,
            is_test=is_test,
            **kwargs
        )
        user.set_password(password)
        user.save()
        if country is not None:
            Profile.objects.filter(user=user).update(country=country)
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

    @classmethod
    def get_1pixel_jpg_image_data(self):
        current_dir = os.path.dirname(os.path.realpath(__file__))
        image_file = os.path.join(current_dir, 'data', 'images', '1x1_pixel.jpg')
        with open(image_file, 'rb') as f:
            return f.read()
