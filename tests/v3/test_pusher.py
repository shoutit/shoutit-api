# -*- coding: utf-8 -*-
import json

from mock import patch
from django_dynamic_fixture import G

from shoutit_pusher.models import PusherChannel, PusherChannelJoin
from tests.base import BaseTestCase, mocked_pusher, unmocked_pusher


class PusherAuthTestCase(BaseTestCase):
    url_name_auth = 'pusher-auth'
    url_name_webhooh = 'pusher-webhook'

    @classmethod
    def setUpTestData(cls):
        cls.user = cls.create_user()
        cls.channel_name = 'private-channel'

    def test_pusher_auth_noauth(self):
        resp = self.client.post(self.reverse(self.url_name_auth))
        self.assert401(resp)

    def test_pusher_valid_data_received(self):
        mocked_pusher.authenticate.reset_mock()
        self.login(self.user)
        resp = self.client.post(
            self.reverse(self.url_name_auth),
            {'channel_name': self.channel_name, 'socket_id': "1234.12"},
            format='json')
        self.assert200(resp)
        self.assertEqual(mocked_pusher.authenticate.call_count, 1)
        self.assertEqual(json.loads(resp.content.decode()),
                         mocked_pusher.authenticate.return_value)

    @patch.object(mocked_pusher, 'authenticate')
    def test_pusher_invalid_data_received(self, m_auth):
        m_auth.side_effect = ValueError
        self.login(self.user)
        resp = self.client.post(
            self.reverse(self.url_name_auth),
            {'channel_name': self.channel_name, 'socket_id': "1234.12"},
            format='json')
        self.assert400(resp)

    @patch.object(mocked_pusher, 'validate_webhook')
    def test_pusher_webhook_nokey(self, m_validate_webhook):
        m_validate_webhook.side_effect = unmocked_pusher.validate_webhook
        resp = self.client.post(self.reverse(self.url_name_webhooh))
        self.assert400(resp)

    def test_pusher_webhook_no_event(self):
        resp = self.post_webhook()
        self.assert200(resp)
        self.assertEqual(json.loads(resp.content.decode())['status'], 'OK')

    @patch.object(mocked_pusher, 'validate_webhook')
    def test_pusher_webhook_channel_occupied(self, m_validate_webhook):
        m_validate_webhook.return_value = self.get_webhook_data(
            name='channel_occupied')
        resp = self.post_webhook()
        self.assert200(resp)
        self.assertTrue(
            PusherChannel.objects.filter(name=self.channel_name).exists())

    @patch.object(mocked_pusher, 'validate_webhook')
    def test_pusher_webhook_channel_vacated(self, m_validate_webhook):
        G(PusherChannel, name=self.channel_name)
        m_validate_webhook.return_value = self.get_webhook_data(
            name='channel_vacated')
        resp = self.post_webhook()
        self.assert200(resp)
        self.assertFalse(
            PusherChannel.objects.filter(name=self.channel_name).exists())

    @patch.object(mocked_pusher, 'validate_webhook')
    def test_pusher_webhook_member_added(self, m_validate_webhook):
        m_validate_webhook.return_value = self.get_webhook_data(
            name='member_added')
        resp = self.post_webhook()
        self.assert200(resp)
        self.assertTrue(PusherChannelJoin.objects.filter(
            channel__name=self.channel_name, user=self.user).exists())

    @patch.object(mocked_pusher, 'validate_webhook')
    def test_pusher_webhook_member_removed(self, m_validate_webhook):
        channel = G(PusherChannel, name=self.channel_name)
        G(PusherChannelJoin, channel=channel, user=self.user)
        m_validate_webhook.return_value = self.get_webhook_data(
            name='member_removed')
        resp = self.post_webhook()
        self.assert200(resp)
        self.assertFalse(PusherChannelJoin.objects.filter(
            channel__name=self.channel_name, user=self.user).exists())

    def post_webhook(self):
        return self.client.post(self.reverse(self.url_name_webhooh),
                                HTTP_X_PUSHER_KEY='key',
                                HTTP_X_PUSHER_SIGNATURE='sign')

    def get_webhook_data(self, name):
        return {'events': [{
            'user_id': str(self.user.pk),
            'name': name,
            'channel': self.channel_name
        }]}
