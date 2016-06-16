# -*- coding: utf-8 -*-
from mock import patch
from django.test import override_settings
from django_dynamic_fixture import G, F
from push_notifications import apns, gcm

from common.constants import (
    CONVERSATION_TYPE_CHAT, CONVERSATION_TYPE_PUBLIC_CHAT,
    NOTIFICATION_TYPE_STATS_UPDATE, NOTIFICATION_TYPE_MESSAGE,
    MESSAGE_ATTACHMENT_TYPE_MEDIA, MESSAGE_ATTACHMENT_TYPE_SHOUT,
    MESSAGE_ATTACHMENT_TYPE_PROFILE, MESSAGE_ATTACHMENT_TYPE_LOCATION)
from shoutit.models import Conversation, Message, Notification
from shoutit.models.auth import APNSDevice, GCMDevice
from tests.base import BaseTestCase, mocked_pusher
from .base import DetailMixin


class ConversationReplyProfileTestCase(DetailMixin, BaseTestCase):
    url_name = 'conversation-reply'

    @classmethod
    def setUpTestData(cls):
        cls.user1 = cls.create_user()
        cls.user2 = cls.create_user(username='john')
        cls.c1 = G(Conversation, type=CONVERSATION_TYPE_CHAT,
                   creator=cls.user1, users=[cls.user1, cls.user2])

    def test_get_unknown_unauth(self):
        resp = self.client.post(self.get_url(1))
        self.assert401(resp)

    def test_message_is_created(self):
        """
        Message with only text is created
        """
        self.login(self.user1)
        resp = self.client.post(self.get_url(self.c1.pk), {
            'text': 'Message text',
        })
        self.assert201(resp)
        self.assertTrue(Message.objects.filter(text='Message text').exists())

    def test_message_with_unknown_attachment_is_forbidden(self):
        """
        Creation of message with unknown attachment is forbidden
        """
        self.login(self.user1)
        resp = self.client.post(self.get_url(self.c1.pk), {
            'text': 'm1',
            'attachments': [{'unknown': {}}]
        })
        self.assert400(resp)
        self.assertFalse(Message.objects.filter(text='m1').exists())

    def test_create_message_without_text_forbidden(self):
        """
        Creation of message with empty text and without attachments
        is forbidden
        """
        self.login(self.user1)
        resp = self.client.post(self.get_url(self.c1.pk), {'text': ''})
        self.assert400(resp)

    def test_message_shout_attachmet_is_saved(self):
        """
        Shout attachment is saved in message
        """
        shout = self.create_shout(
            user=self.user1, category=F(name='velo'), item=F(name='Marin'))
        self.login(self.user1)
        resp = self.client.post(self.get_url(self.c1.pk), {
            'text': 'm1',
            'attachments': [
                {
                    'shout': {'id': shout.pk}
                },
            ]
        })
        attachment = self.assert_one_attachment(
            resp, 'm1', MESSAGE_ATTACHMENT_TYPE_SHOUT)
        self.assertEqual(attachment.attached_object.pk, shout.pk)

    def test_message_profile_attachmet_is_saved(self):
        """
        Profile attachment is saved in message
        """
        self.login(self.user1)
        resp = self.client.post(self.get_url(self.c1.pk), {
            'text': 'm1',
            'attachments': [
                {
                    'profile': {'id': self.user1.profile.pk}
                },
            ]
        })
        attachment = self.assert_one_attachment(
            resp, 'm1', MESSAGE_ATTACHMENT_TYPE_PROFILE)
        self.assertEqual(attachment.attached_object.pk, self.user1.profile.pk)

    def test_message_location_attachmet_is_saved(self):
        """
        Location attachment is saved in message
        """
        self.login(self.user1)
        resp = self.client.post(self.get_url(self.c1.pk), {
            'text': 'm1',
            'attachments': [
                {
                    'location': self.COORDINATES['USA']
                },
            ]
        })
        attachment = self.assert_one_attachment(
            resp, 'm1', MESSAGE_ATTACHMENT_TYPE_LOCATION)
        obj = attachment.attached_object
        self.assertEqual(obj.longitude, self.COORDINATES['USA']['longitude'])
        self.assertEqual(obj.latitude, self.COORDINATES['USA']['latitude'])

    def test_message_location_lack_of_coordinate_is_forbidden(self):
        """
        Location with only one coordinate is forbidden
        """
        self.login(self.user1)
        resp = self.client.post(self.get_url(self.c1.pk), {
            'text': 'm1',
            'attachments': [
                {
                    'location': {'latitude': 71.18}
                },
            ]
        })
        self.assert400(resp)

    def test_message_media_attachmet_is_saved(self):
        """
        Media attachment is saved in message
        """
        self.login(self.user1)
        image_urls = ['http://s3.com/image1.png', 'http://s3.com/image1.png']
        videos = [
            self.get_video_data(url='http://yout.com/v1'),
            self.get_video_data(url='http://yout.com/v2'),
        ]
        resp = self.client.post(self.get_url(self.c1.pk), {
            'text': 'm1',
            'attachments': [
                {
                    'images': image_urls,
                    'videos': videos,
                }
            ]
        })
        attachment = self.assert_one_attachment(
            resp, 'm1', MESSAGE_ATTACHMENT_TYPE_MEDIA)
        self.assertEqual(attachment.images, image_urls)
        self.assertEqual(attachment.videos.count(), len(videos))
        self.assertEqual(set(attachment.videos.values_list('url', flat=True)),
                         set(v['url'] for v in videos))

    def test_empty_media_attachment_is_forbidden(self):
        """
        Media attachment without images and videos is forbidden
        """
        self.login(self.user1)
        resp = self.client.post(self.get_url(self.c1.pk), {
            'text': 'm1',
            'attachments': [
                {
                    'images': [],
                    'videos': [],
                }
            ]
        })
        self.assert400(resp)

    def test_message_multiple_attachmets_are_saved(self):
        """
        Two attachment of different types are saved in message
        """
        self.login(self.user1)
        resp = self.client.post(self.get_url(self.c1.pk), {
            'text': 'm1',
            'attachments': [
                {
                    'profile': {'id': self.user1.profile.pk}
                },
                {
                    'location': self.COORDINATES['USA']
                },
            ]
        })
        self.assert201(resp)
        attachments = Message.objects.get(text='m1').attachments.all()
        self.assertEqual(len(attachments), 2)
        self.assertEqual(set(attachments.values_list('type', flat=True)),
                         set(map(int, [MESSAGE_ATTACHMENT_TYPE_PROFILE,
                                       MESSAGE_ATTACHMENT_TYPE_LOCATION])))

    @patch.object(mocked_pusher, 'trigger')
    def test_message_reply_new_message_pusher_event(self, m_trigger):
        """
        On message reply 'new_message' event is triggered on pusher
        """
        self.login(self.user1)
        m_trigger.reset_mock()
        self.client.post(self.get_url(self.c1.pk), {'text': 'm1'})
        self.assert_pusher_event(
            m_trigger, str(NOTIFICATION_TYPE_MESSAGE),
            channel_name=self.get_pusher_conversation_channel_name(self.c1.pk))

    def test_user_is_added_to_conversation_on_message_reply(self):
        """
        User is added to public chat on message reply
        """
        conv = G(Conversation, type=CONVERSATION_TYPE_PUBLIC_CHAT,
                 creator=self.user1)
        self.login(self.user2)
        self.client.post(self.get_url(conv.pk), {'text': 'm1'})
        self.assertIn(self.user2,
                      Conversation.objects.get(pk=conv.pk).users.all())

    def test_chat_contributors_notification_on_message_reply(self):
        """
        Chat contributors are notified about new message,
        except message creator
        """
        self.login(self.user1)
        self.client.post(self.get_url(self.c1.pk), {'text': 'm1'})
        self.assertEqual(
            Notification.objects.filter(
                to_user=self.user2, type=int(NOTIFICATION_TYPE_MESSAGE),
                is_read=False).count(), 1)
        self.assertEqual(
            Notification.objects.filter(
                to_user=self.user1, type=int(NOTIFICATION_TYPE_MESSAGE),
                is_read=False).count(), 0)

    @patch.object(mocked_pusher, 'trigger')
    def test_new_message_reply_stats_update_pusher_event(self, m_trigger):
        """
        Stats update pusher event is triggered on message reply
        """
        self.login(self.user1)
        m_trigger.reset_mock()
        self.client.post(self.get_url(self.c1.pk), {'text': 'm1'})
        self.assert_pusher_event(
            m_trigger, str(NOTIFICATION_TYPE_STATS_UPDATE),
            channel_name=self.get_pusher_user_channel_name(self.user2.pk),
            call_count=1)

    @patch.object(mocked_pusher, 'trigger')
    def test_new_message_reply_profile_pusher_event(self, m_trigger):
        """
        Profile pusher event is triggered on message reply
        """
        self.login(self.user1)
        m_trigger.reset_mock()
        self.client.post(self.get_url(self.c1.pk), {'text': 'm1'})
        self.assert_pusher_event(
            m_trigger, str(NOTIFICATION_TYPE_MESSAGE),
            channel_name=self.get_pusher_user_channel_name(self.user2.pk),
            attached_object_partial_dict={'text': 'm1'},
            call_count=3)

    @override_settings(USE_PUSH=True)
    @patch.object(apns, 'apns_send_bulk_message')
    def test_apns_push_event_on_message_reply(self, m_apns_bulk):
        """
        push event is sent if no pusher channel exist
        """
        self.login(self.user1)
        device = G(APNSDevice, user=self.user2, api_version=self.url_namespace)
        self.client.post(self.get_url(self.c1.pk), {'text': 'm1'})
        call_kwargs = self.assert_ios_badge_set(
            m_apns_bulk, [device.registration_id], badge=1, call_count=1)
        self.assertIn('m1', call_kwargs['alert']['body'])

    @override_settings(USE_PUSH=True)
    @patch.object(gcm, 'gcm_send_bulk_message')
    def test_gcm_push_event_on_message_reply(self, m_gcm_bulk):
        """
        gcm event is sent if no pusher channel exist
        """
        self.login(self.user1)
        device = G(GCMDevice, user=self.user2, api_version=self.url_namespace)
        self.client.post(self.get_url(self.c1.pk), {'text': 'm1'})
        call_kwargs = self.assert_gcm_sent(
            m_gcm_bulk, [device.registration_id])
        self.assertIn('m1', call_kwargs['data']['body'])

    def assert_one_attachment(self, resp, message_text, attachment_type):
        self.assert201(resp)
        message_attachments = Message.objects.get(
            text=message_text).attachments.all()
        self.assertEqual(len(message_attachments), 1)
        attachment = message_attachments[0]
        self.assertEqual(attachment.type, int(attachment_type))
        return attachment
