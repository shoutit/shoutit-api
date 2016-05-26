# -*- coding: utf-8 -*-
import json

from mock import patch
from django_dynamic_fixture import G, N
from push_notifications import apns

from shoutit.models import Notification
from shoutit.models.auth import APNSDevice
from common.constants import (
    NOTIFICATION_TYPE_MESSAGE, NOTIFICATION_TYPE_LISTEN,
    NOTIFICATION_TYPE_BROADCAST, NOTIFICATION_TYPE_STATS_UPDATE)
from tests.base import BaseTestCase, mocked_pusher


class NotificationsTestCase(BaseTestCase):
    url_name_list = 'notification-list'
    url_name_read = 'notification-read'
    url_name_reset = 'notification-reset'

    @classmethod
    def setUpTestData(cls):
        cls.user = cls.create_user()
        cls.another_user = cls.create_user(username='john')

        cls.device = G(APNSDevice, user=cls.user)

        cls.n1 = N(Notification, to_user=cls.user, type=NOTIFICATION_TYPE_MESSAGE)
        cls.n1.attached_object = cls.another_user
        cls.n1.save()

        cls.n2 = N(Notification, to_user=cls.user, type=NOTIFICATION_TYPE_LISTEN)
        cls.n2.attached_object = cls.another_user
        cls.n2.save()

        cls.n3 = G(Notification, to_user=cls.user,
                   type=NOTIFICATION_TYPE_BROADCAST)

        cls.n4 = G(Notification, to_user=cls.another_user,
                   type=NOTIFICATION_TYPE_LISTEN)

        cls.notifications = [cls.n1, cls.n2, cls.n3, cls.n4]
        cls.user_notifications = [cls.n2, cls.n3]

    # list

    def test_notifications_list_nodata(self):
        resp = self.client.get(self.reverse(self.url_name_list))
        self.assert401(resp)

    def test_notification_list(self):
        self.client.login(username=self.user.username, password='123')
        resp = self.client.get(self.reverse(self.url_name_list))
        self.assert200(resp)
        self.assert_ids_equal(json.loads(resp.content)['results'],
                              self.user_notifications)

    # reset

    def test_notification_reset_marked_as_read(self):
        self.client.login(username=self.user.username, password='123')
        self._change_read(self.notifications, False)
        resp = self.client.post(self.reverse(self.url_name_reset))
        self.assert202(resp)
        self.assert_ids_equal(
            Notification.objects.filter(is_read=True).values('id'),
            self.user_notifications)

    @patch.object(mocked_pusher, 'trigger')
    def test_notification_reset_pusher_event_sent(self, m_trigger):
        self.client.login(username=self.user.username, password='123')
        m_trigger.reset_mock()
        self.client.post(self.reverse(self.url_name_reset))
        self.assert_pusher_event(m_trigger,
                                 str(NOTIFICATION_TYPE_STATS_UPDATE))

    @patch.object(apns, 'apns_send_bulk_message')
    def test_notification_reset_ios_badge_set(self, m_apns_bulk):
        self.client.login(username=self.user.username, password='123')
        self.client.post(self.reverse(self.url_name_reset))
        self.assert_ios_badge_set(m_apns_bulk, [self.device.registration_id],
                                  badge=0)

    def test_notifications_reset_unknown(self):
        resp = self.client.get(self.reverse(self.url_name_reset))
        self.assert401(resp)

    # read

    def test_notification_read_unknown(self):
        resp = self.client.post(
            self.reverse(self.url_name_read, kwargs={'id': 1}))
        self.assert401(resp)

    def test_notification_read_bad_id(self):
        self.client.login(username=self.user.username, password='123')
        resp = self.client.post(
            self.reverse(self.url_name_read, kwargs={'id': 1}))
        self.assert400(resp)

    def test_notification_read_changed(self):
        self._change_read([self.n2], False)
        self.client.login(username=self.user.username, password='123')
        resp = self.client.post(
            self.reverse(self.url_name_read, kwargs={'id': self.n2.pk}))
        self.assert202(resp)
        self.assertTrue(Notification.objects.get(pk=self.n2.pk).is_read)

    @patch.object(mocked_pusher, 'trigger')
    def test_notification_read_event_sent(self, m_trigger):
        self._change_read(self.user_notifications, False)
        self.client.login(username=self.user.username, password='123')
        m_trigger.reset_mock()
        self.client.post(
            self.reverse(self.url_name_read, kwargs={'id': self.n2.pk}))
        self.assert_pusher_event(
            m_trigger, str(NOTIFICATION_TYPE_STATS_UPDATE),
            attached_object_partial_dict={
                'unread_notifications_count': 1,
                'unread_conversations_count': 0,
            })

    @patch.object(apns, 'apns_send_bulk_message')
    def test_notification_ios_badge_set(self, m_apns_bulk):
        self._change_read(self.user_notifications, False)
        self.client.login(username=self.user.username, password='123')
        self.client.post(
            self.reverse(self.url_name_read, kwargs={'id': self.n2.pk}))
        self.assert_ios_badge_set(m_apns_bulk, [self.device.registration_id],
                                  badge=1)

    def _change_read(self, notifications, is_read):
        for n in notifications:
            n.is_read = is_read
            n.save()
