# -*- coding: utf-8 -*-
from mock import patch
from django_dynamic_fixture import G
from push_notifications import apns

from common.constants import (
    CONVERSATION_TYPE_CHAT, NOTIFICATION_TYPE_STATS_UPDATE,
    NOTIFICATION_TYPE_READ_BY
)
from shoutit.models import Conversation, Message, MessageRead, Notification
from shoutit.models.auth import APNSDevice
from tests.base import BaseTestCase, mocked_pusher
from .base import DetailMixin


class MarkReadMixin(DetailMixin):
    http_method = 'get'
    status_code = 200

    @classmethod
    def setUpTestData(cls):
        cls.user1 = cls.create_user()
        cls.user2 = cls.create_user(username='john')
        cls.device = G(APNSDevice, user=cls.user1)
        cls.c1 = G(Conversation, type=CONVERSATION_TYPE_CHAT,
                   creator=cls.user1, users=[cls.user1])

    def test_notification_marked_as_read(self):
        """
        On accessing resource message notifications are marked as read
        """
        G(Message, user=self.user2, conversation=self.c1)
        self.login(self.user1)
        conv_notifications = Notification.objects.filter(
            message__conversation=self.c1)
        # currently no read notifications exists
        self.assertFalse(conv_notifications.filter(is_read=True).exists())
        self._do_request()
        self.assertFalse(conv_notifications.exclude(is_read=True).exists())
        self.assertTrue(conv_notifications.filter(is_read=True).exists())

    @patch.object(mocked_pusher, 'trigger')
    def test_no_unread_messages_no_pusher(self, m_trigger):
        """
        Pusher event is not triggered, when no unread messages
        """
        self.login(self.user1)
        m_trigger.reset_mock()
        self._do_request()
        self.assertFalse(m_trigger.called)

    @patch.object(mocked_pusher, 'trigger')
    def test_pusher_stats_update(self, m_trigger):
        """
        Stats update event is sent to pusher, when unread messages exists
        """
        G(Message, user=self.user2, conversation=self.c1)
        self.login(self.user1)
        m_trigger.reset_mock()
        self._do_request()
        self.assert_pusher_event(
            m_trigger, str(NOTIFICATION_TYPE_STATS_UPDATE),
            channel_name=self.get_pusher_user_channel_name(self.user1.pk))

    @patch.object(apns, 'apns_send_bulk_message')
    def test_ios_badge(self, m_apns_bulk):
        """
        IOS badge is set, when unread messages exists
        """
        G(Message, user=self.user2, conversation=self.c1)
        self.login(self.user1)
        self._do_request()
        self.assert_ios_badge_set(m_apns_bulk, [self.device.registration_id],
                                  badge=1)

    def test_message_read_created(self):
        """
        Messages by other users are read, if weren't read before
        """
        m = G(Message, user=self.user2, conversation=self.c1)
        self.login(self.user1)
        self._do_request()
        self.assertEqual(
            MessageRead.objects.filter(
                user=self.user1, message=m, conversation=self.c1).count(), 1)

    @patch.object(mocked_pusher, 'trigger')
    def test_pusher_new_read_by(self, m_trigger):
        """
        New read by event is sent to pusher for every unread message
        """
        m1 = G(Message, user=self.user2, conversation=self.c1)
        m2 = G(Message, user=self.user2, conversation=self.c1)
        self.login(self.user1)
        m_trigger.reset_mock()
        self._do_request()
        args1 = self._assert_read_by_pusher_event(m_trigger, self.c1.pk, 1)
        args2 = self._assert_read_by_pusher_event(m_trigger, self.c1.pk, 2)
        # check, that pusher event contains message in attached_object
        self.assertEqual(set([m1.id, m2.id]),
                         set([args1[2]['id'], args2[2]['id']]))

    def test_unread_conversations_count(self):
        """
        test that count is recalculated on read
        """
        m = G(Message, user=self.user2, conversation=self.c1, unread_conversations_count=1)

        self.login(self.user1)
        self._do_request()
        self.assertEqual(
            MessageRead.objects.filter(
                user=self.user1, message=m, conversation=self.c1).count(), 1)

        self.user1 = self.user1._meta.model.objects.get(id=self.user1.id)
        self.assertEqual(self.user1.unread_conversations_count, 0)

    def _do_request(self):
        request_method = getattr(self.client, self.http_method)
        resp = request_method(self.get_url(self.c1.pk))
        self.assertEqual(resp.status_code, self.status_code)
        return resp

    def _assert_read_by_pusher_event(self, m_trigger, conv_id, call_count=0):
        return self.assert_pusher_event(
            m_trigger, str(NOTIFICATION_TYPE_READ_BY),
            channel_name=self.get_pusher_conversation_channel_name(conv_id),
            call_count=call_count)


class ConversationMessagesMarkedReadTestCase(MarkReadMixin, BaseTestCase):
    url_name = 'conversation-messages'


class ConversationReadMarkedAsReadTestCase(MarkReadMixin, BaseTestCase):
    url_name = 'conversation-read'
    http_method = 'post'
    status_code = 202


class ConversationReadTestCase(DetailMixin, BaseTestCase):
    url_name = 'conversation-read'

    @classmethod
    def setUpTestData(cls):
        cls.user1 = cls.create_user()
        cls.user2 = cls.create_user(username='john')
        cls.c1 = G(Conversation, type=CONVERSATION_TYPE_CHAT,
                   creator=cls.user1, users=[cls.user1, cls.user2])

    def test_get_unknown_unauth(self):
        resp = self.client.post(self.get_url(1))
        self.assert401(resp)

    def test_last_message_marked_as_unread(self):
        """
        Only last message is marked as unread
        """
        m1 = G(Message, user=self.user2, conversation=self.c1)
        m2 = G(Message, user=self.user2, conversation=self.c1)
        mr1 = MessageRead.objects.create(user=self.user1, message=m1,
                                         conversation=self.c1)
        mr2 = MessageRead.objects.create(user=self.user1, message=m2,
                                         conversation=self.c1)
        self.update_auto_dt_field(mr1, 'created_at', self.dt_before(days=2))
        self.update_auto_dt_field(mr2, 'created_at', self.dt_before(days=1))
        self.login(self.user1)
        resp = self.client.delete(self.get_url(self.c1.pk))
        self.assert202(resp)
        self.assertTrue(MessageRead.objects.filter(pk=mr1.pk).exists())
        self.assertFalse(MessageRead.objects.filter(pk=mr2.pk).exists())

    def test_unread_message_allowed_to_chat_contributor(self):
        """
        Chat contributor is allowed to mark conversation as unread
        """
        self.login(self.user2)
        resp = self.client.delete(self.get_url(self.c1.pk))
        self.assert202(resp)
