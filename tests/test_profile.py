"""
Tests for User model (profile) integration.
"""
from .base import BaseTestCase
from shoutit.controllers.notifications_controller import (
    get_unread_conversations_count
)
from shoutit.controllers.message_controller import send_message



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
        cls.message_text = 'There is something I need to tell you'

    def test_update_notifications(self):
        # TODO new messages also trigger Notifications, so I might just test both at once
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
