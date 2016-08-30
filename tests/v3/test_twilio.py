# -*- coding: utf-8 -*-
from django.utils.timezone import now, timedelta

from django_dynamic_fixture import G

from shoutit_twilio.models import VideoClient
from tests.base import BaseTestCase


class BaseTwilioTestCase(BaseTestCase):
    longMessage = True

    @classmethod
    def get_user(cls):
        user = getattr(cls, 'user', None)
        if user is None:
            user = cls.create_user()
        return user

    @classmethod
    def setup_users(cls):
        cls.user = cls.create_user()
        cls.user2 = cls.create_user(
            username='user2',
            first_name='Hank',
        )

    @classmethod
    def setup_video_client(cls, user=None):
        if user is None:
            user = cls.get_user()
        cls.video_client = G(VideoClient, user=user)


class TwilioProfileTestCase(BaseTwilioTestCase):
    url_name = 'twilio-profile'

    @classmethod
    def setUpTestData(cls):
        cls.setup_users()
        cls.setup_video_client()

    def test_twilio_profile_smoke(self):
        resp = self.client.get(self.reverse(self.url_name))
        self.assert401(resp)

    def test_twilio_profile_noidentity(self):
        self.login(self.user)
        data = {}
        resp = self.client.get(self.reverse(self.url_name), data)
        self.assert400(resp)

    def test_video_call_identity_does_not_exist(self):
        self.login(self.user)
        data = {'identity': self.video_client.identity}
        self.video_client.delete()
        resp = self.client.get(self.reverse(self.url_name), data)
        self.assert400(resp)

    def test_video_call_invalid_identity(self):
        self.login(self.user)
        data = {'identity': 'invalid'}
        resp = self.client.get(self.reverse(self.url_name), data)
        self.assert400(resp)

    def test_profile(self):
        self.login(self.user)
        data = {
            'identity': self.video_client.identity
        }
        resp = self.client.get(self.reverse(self.url_name), data)
        self.assert200(resp)
        self.assertEqual(
            self.decode_json(resp).get('id', ''),
            str(self.user.id),
            msg='Should have retrieved the user belonging to the video client.'
        )


class TwilioVideoAuthTestCase(BaseTwilioTestCase):
    url_name = 'twilio-video-auth'

    @classmethod
    def setUpTestData(cls):
        cls.setup_users()

    def test_twilio_video_auth_smoke(self):
        resp = self.client.post(self.reverse(self.url_name))
        self.assert401(resp)

    def test_video_auth(self):
        self.login(self.user)
        self.assertEqual(
            VideoClient.objects.count(),
            0,
            msg='There should be no video clients before the post.'
        )
        resp = self.client.post(self.reverse(self.url_name))
        self.assert200(resp)
        self.assertEqual(
            self.decode_json(resp).get('identity', ''),
            str(self.user.video_client.identity),
            msg='Should return a new video client for the user.'
        )
        self.assertEqual(
            VideoClient.objects.count(),
            1,
            msg='The endpoint should have created a new video client.'
        )

        resp = self.client.post(self.reverse(self.url_name))
        self.assert200(resp)
        self.assertEqual(
            self.decode_json(resp).get('identity', ''),
            str(self.user.video_client.identity),
            msg='Should return the existing client for the user.'
        )
        self.assertEqual(
            VideoClient.objects.count(),
            1,
            msg='The endpoint should not have created a new video client.'
        )

        self.user.video_client.created_at = now() - timedelta(
            seconds=self.user.video_client.ttl, days=1
        )
        self.user.video_client.save()

        resp = self.client.post(self.reverse(self.url_name))
        self.assert200(resp)
        self.assertEqual(
            self.decode_json(resp).get('identity', ''),
            VideoClient.objects.get(user=self.user).identity,
            msg='Should return a new client for the user.'
        )
        self.assertEqual(
            VideoClient.objects.count(),
            1,
            msg=(
                'The endpoint should have created a new video client, because'
                ' the old one expired.'
            )
        )


class TwilioVideoCallTestCase(BaseTwilioTestCase):
    url_name = 'twilio-video-call'

    @classmethod
    def setUpTestData(cls):
        cls.setup_users()
        cls.setup_video_client()

    def test_twilio_video_call_smoke(self):
        resp = self.client.post(self.reverse(self.url_name))
        self.assert401(resp)

    def test_video_call_identity_does_not_exist(self):
        self.login(self.user)
        data = {'identity': self.video_client.identity}
        self.video_client.delete()
        resp = self.client.post(self.reverse(self.url_name), data)
        self.assert400(resp)

    def test_video_call_invalid_identity(self):
        self.login(self.user)
        data = {'identity': 'invalid'}
        resp = self.client.post(self.reverse(self.url_name), data)
        self.assert400(resp)

    def test_video_call_noidentity(self):
        self.login(self.user)
        data = {}
        resp = self.client.post(self.reverse(self.url_name), data)
        self.assert400(resp)

    def test_video_call(self):
        self.login(self.user)
        data = {'identity': self.video_client.identity}
        resp = self.client.post(self.reverse(self.url_name), data)
        self.assert200(resp)

        self.login(self.user)
        data = {'identity': self.video_client.identity, 'missed': True}
        resp = self.client.post(self.reverse(self.url_name), data)
        self.assert200(resp)


class TwilioVideoIdentityTestCase(BaseTwilioTestCase):
    url_name = 'twilio-video-identity'

    @classmethod
    def setUpTestData(cls):
        cls.setup_users()

    def test_twilio_video_identity_smoke(self):
        resp = self.client.get(self.reverse(self.url_name))
        self.assert401(resp)

    def test_video_identity(self):
        self.login(self.user)
        self.assertEqual(
            VideoClient.objects.count(),
            0,
            msg='User should not have a video client beforehand.'
        )
        resp = self.client.get(self.reverse(self.url_name), data={'profile': self.user2.username})
        self.assert200(resp)
        self.assertEqual(
            self.decode_json(resp).get('identity', ''),
            self.user2.video_client.identity,
            msg="Should return the right user's identity"
        )
        self.assertEqual(
            VideoClient.objects.count(),
            1,
            msg='Should have created one video client for the user.'
        )

        resp = self.client.get(self.reverse(self.url_name), data={'profile': self.user2.username})
        self.assert200(resp)
        self.assertEqual(
            self.decode_json(resp).get('identity', ''),
            self.user2.video_client.identity,
            msg="Should return the right user's identity"
        )
        self.assertEqual(
            VideoClient.objects.count(),
            1,
            msg='Should have returned the existing client without creating another one.'
        )

    def test_video_identity_invalid(self):
        self.login(self.user)
        # profile is required
        data = {}
        resp = self.client.get(self.reverse(self.url_name), data)
        self.assert400(resp)

        # can't call yourself
        data = {'profile': self.user.username}
        resp = self.client.get(self.reverse(self.url_name), data)
        self.assert400(resp)

        # user doesn't exist
        data = {'profile': 'doesnotexist'}
        resp = self.client.get(self.reverse(self.url_name), data)
        self.assert400(resp)
