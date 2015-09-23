"""
    Shoutit Tests
"""
from __future__ import unicode_literals
from django.core.management import call_command

from django.test import TestCase

from .models import *  # NOQA


class QuestionMethodTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command('fill')
        cls.u1 = User.objects.get(username='syron')
        cls.u2 = User.objects.get(username='mo')

    def test_data_filled(self):
        self.assertIsInstance(self.u1, User)
        self.assertIsInstance(self.u1.profile, Profile)

    def test_user_creation(self):
        """
        was_published_recently() should return False for questions whose
        pub_date is in the future.
        """
        user = User.objects.create_user(username='testuser', password=None)
        self.assertIsInstance(user, User)
