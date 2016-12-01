# -*- coding: utf-8 -*-
from mock import patch
from django_dynamic_fixture import G, N
from push_notifications import apns

from shoutit.models import Notification
from shoutit.models.auth import APNSDevice
from common.constants import (
    NOTIFICATION_TYPE_MESSAGE, NOTIFICATION_TYPE_LISTEN,
    NOTIFICATION_TYPE_BROADCAST, NOTIFICATION_TYPE_STATS_UPDATE,
    NOTIFICATION_TYPE_INCOMING_VIDEO_CALL,
    NOTIFICATION_TYPE_MISSED_VIDEO_CALL)
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

        cls.n1 = cls._create_notif(NOTIFICATION_TYPE_MESSAGE)

        cls.n2 = cls._create_notif(NOTIFICATION_TYPE_LISTEN)
        cls.n3 = cls._create_notif(NOTIFICATION_TYPE_INCOMING_VIDEO_CALL,
                                   attached_object=cls.user.profile)
        cls.n4 = cls._create_notif(NOTIFICATION_TYPE_MISSED_VIDEO_CALL)
        cls.n5 = cls._create_notif(NOTIFICATION_TYPE_BROADCAST,
                                   attached_object=False)

        cls.n6 = cls._create_notif(NOTIFICATION_TYPE_LISTEN,
                                   to_user=cls.another_user)

        cls.user_notifications = [cls.n2, cls.n3, cls.n4, cls.n5]

    # list

    def test_notifications_list_nodata(self):
        resp = self.client.get(self.reverse(self.url_name_list))
        self.assert401(resp)

    def test_notification_list(self):
        self.login(self.user)
        resp = self.client.get(self.reverse(self.url_name_list))
        self.assert200(resp)
        self.assert_ids_equal(self.decode_json(resp)['results'],
                              self.user_notifications)

    # reset

    def test_notification_reset_marked_as_read(self):
        self.login(self.user)
        Notification.objects.all().update(is_read=False)
        resp = self.client.post(self.reverse(self.url_name_reset))
        self.assert202(resp)
        self.assert_ids_equal(
            Notification.objects.filter(is_read=True).values('id'),
            self.user_notifications)

    @patch.object(mocked_pusher, 'trigger')
    def test_notification_reset_pusher_event_sent(self, m_trigger):
        self.login(self.user)
        m_trigger.reset_mock()
        self.client.post(self.reverse(self.url_name_reset))
        self.assert_pusher_event(m_trigger,
                                 str(NOTIFICATION_TYPE_STATS_UPDATE))

    @patch.object(apns, 'apns_send_bulk_message')
    def test_notification_reset_ios_badge_set(self, m_apns_bulk):
        self.login(self.user)
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
        self.login(self.user)
        resp = self.client.post(
            self.reverse(self.url_name_read, kwargs={'id': 1}))
        self.assert400(resp)

    def test_notification_read_changed(self):
        self.n2.save()
        Notification.objects.filter(pk=self.n2.pk).update(is_read=False)
        self.login(self.user)
        resp = self.client.post(
            self.reverse(self.url_name_read, kwargs={'id': self.n2.pk}))
        self.assert202(resp)
        self.assertTrue(Notification.objects.get(pk=self.n2.pk).is_read)

    @patch.object(mocked_pusher, 'trigger')
    def test_notification_read_event_sent(self, m_trigger):
        Notification.objects.all().update(is_read=False)
        self.user.unread_notifications_count = Notification.objects.filter(to_user=self.user).count()
        self.user.save()
        self.login(self.user)
        m_trigger.reset_mock()
        self.client.post(
            self.reverse(self.url_name_read, kwargs={'id': self.n2.pk}))
        # could not deal with mocks here fas enough, it seems that model has unread_notifications_count set to 3
        # but here in test it raises an error that 5 is not equals 3, not sure where is 5 taken, the only thing
        # equals 5 is total count but not actual
        self.assert_pusher_event(
            m_trigger, str(NOTIFICATION_TYPE_STATS_UPDATE),
            attached_object_partial_dict={
                'unread_notifications_count': 3,
                'unread_conversations_count': 0,
            })

    @patch.object(apns, 'apns_send_bulk_message')
    def test_notification_ios_badge_set(self, m_apns_bulk):
        Notification.objects.all().update(is_read=False)
        self.login(self.user)
        self.client.post(
            self.reverse(self.url_name_read, kwargs={'id': self.n2.pk}))
        self.assert_ios_badge_set(m_apns_bulk, [self.device.registration_id],
                                  badge=3)

    @classmethod
    def _create_notif(cls, n_type, to_user=None, attached_object=None):
        to_user = to_user or cls.user
        n = N(Notification, to_user=to_user, type=n_type)
        attached_object = attached_object or cls.another_user
        if attached_object:
            n.attached_object = attached_object
            n.save()
        return n
