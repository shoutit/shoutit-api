# -*- coding: utf-8 -*-
from tests.base import BaseTestCase


class TwilioProfileTestCase(BaseTestCase):
    url_name = 'twilio-profile'

    def test_twilio_profile_smoke(self):
        resp = self.client.get(self.reverse(self.url_name))
        self.assert401(resp)


class TwilioVideoAuthTestCase(BaseTestCase):
    url_name = 'twilio-video-auth'

    def test_twilio_video_auth_smoke(self):
        resp = self.client.post(self.reverse(self.url_name))
        self.assert401(resp)


class TwilioVideoCallTestCase(BaseTestCase):
    url_name = 'twilio-video-call'

    def test_twilio_video_call_smoke(self):
        resp = self.client.post(self.reverse(self.url_name))
        self.assert401(resp)


class TwilioVideoIdentityTestCase(BaseTestCase):
    url_name = 'twilio-video-identity'

    def test_twilio_video_identity_smoke(self):
        resp = self.client.get(self.reverse(self.url_name))
        self.assert401(resp)
