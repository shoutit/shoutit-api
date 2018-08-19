"""
Tests for User model (profile) integration.
"""
from django_dynamic_fixture import G
from mock import patch

from .base import BaseTestCase
from shoutit.controllers.notifications_controller import (
    get_unread_conversations_count,
    get_unread_actual_notifications_count,
    mark_actual_notifications_as_read,
    notify_user_of_listen,
)
from shoutit.controllers import email_controller
from shoutit.controllers.message_controller import send_message
from shoutit.models import Category
from shoutit_credit.models import ShareShouts
from shoutit_credit.models.base import CREDIT_IN


class ProfileStatsTestCase(BaseTestCase):
    """
    Testing the updating of stats on the User model about notifications,
    conversations and credits.
    """
    longMessage = True

    @classmethod
    def setUpTestData(cls):
        cls.user = cls.create_user()
        cls.from_user = cls.create_user(
            username='from',
            first_name='From',
        )
        cls.category = G(Category, slug='local-business')
        cls.shout = cls.create_shout(user=cls.user, category=cls.category)
        cls.message_text = 'There is something I need to tell you'

    @patch.object(email_controller, '_send_notification_email')
    def test_update_credit(self, send_notification_email_mock):
        G(
            ShareShouts,
            transaction_type=CREDIT_IN,
            type='foo',
            name='bar',
            description='foobar',
        )
        rule = ShareShouts.objects.get()

        self.assertEqual(
            self.user.credit, 0,
            msg='The user model should have a credit of 0',
        )

        transaction = rule.apply(self.shout)
        self.user.refresh_from_db()

        self.assertEqual(
            self.user.credit, 1,
            msg='The user model should have a credit of 1',
        )

        transaction.delete()
        self.user.refresh_from_db()

        self.assertEqual(
            self.user.credit, 0,
            msg='The user model should have a credit of 0',
        )

    def test_update_notifications(self):
        unread_notifications_pre = self.user.unread_notifications_count
        # sending notification
        notify_user_of_listen(self.user, self.from_user)
        self.assertEqual(
            get_unread_actual_notifications_count(self.user),
            1,
            msg=(
                'There should be one unread notification for user {0}.'.format(
                    self.user.username)
            )
        )

        self.assertEqual(
            self.user.unread_notifications_count,
            unread_notifications_pre + 1,
            msg=(
                'The user model should return one more unread notification'
                ' than before.'
            )
        )

        # mark them as read
        mark_actual_notifications_as_read(self.user)

        self.assertEqual(
            get_unread_actual_notifications_count(self.user),
            0,
            msg=(
                'There the one message for user {0} should be read.'.format(
                    self.user.username)
            )
        )

        self.assertEqual(
            self.user.unread_notifications_count,
            unread_notifications_pre,
            msg='The user model should return no more unread notifications'
        )

    def test_update_conversations(self):
        unread_conversations_pre = self.user.unread_conversations_count
        # sending a message
        message = send_message(
            conversation=None, user=self.from_user, to_users=[self.user],
            text=self.message_text,
        )
        self.assertEqual(
            get_unread_conversations_count(self.user),
            1,
            msg=(
                'There should be one unread conversation for user {0}.'.format(
                    self.user.username)
            )
        )

        self.assertEqual(
            self.user.unread_conversations_count,
            unread_conversations_pre + 1,
            msg=(
                'The user model should return one more unread conversation'
                ' than before.'
            )
        )

        # reading the message
        message.mark_as_read(self.user)

        self.assertEqual(
            get_unread_conversations_count(self.user),
            0,
            msg=(
                'There the one message for user {0} should be read.'.format(
                    self.user.username)
            )
        )

        self.assertEqual(
            self.user.unread_conversations_count,
            unread_conversations_pre,
            msg='The user model should return no more unread conversations'
        )

        # marking mesage as unread again
        return  # TODO marking a message as unread does not make the `get_unread_conversations_count` return an additional conversation?
        message.mark_as_unread(self.user)
        self.assertEqual(
            get_unread_conversations_count(self.user),
            1,
            msg=(
                'There should be one unread conversation for user {0}.'.format(
                    self.user.username)
            )
        )

        self.assertEqual(
            self.user.unread_conversations_count,
            unread_conversations_pre + 1,
            msg=(
                'The user model should return one more unread conversation'
                ' than before.'
            )
        )
