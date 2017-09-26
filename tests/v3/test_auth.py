# -*- coding: utf-8 -*-
import time
from datetime import datetime, timedelta
from json import loads

import responses
from django.contrib.auth import get_user_model
from django_dynamic_fixture import G
from provider.oauth2.models import RefreshToken, Client

from common.constants import TOKEN_TYPE_RESET_PASSWORD, TOKEN_TYPE_EMAIL, DEFAULT_LOCATION
from shoutit.controllers.facebook_controller import FB_GRAPH_ACCESS_TOKEN_URL
from shoutit.models import AuthToken, Category, DBCLConversation, ConfirmToken, Page, PageCategory, Profile
from tests.base import BaseTestCase

User = get_user_model()


class ChangePasswordTestCase(BaseTestCase):
    url_name = 'shoutit_auth-change-password'
    longMessage = True

    @classmethod
    def setUpTestData(cls):
        cls.user = cls.create_user()

    def test_unauth_no_data(self):
        resp = self.client.post(self.reverse(self.url_name))
        self.assert401(resp)

    def test_no_password(self):
        self.login(self.user)
        data = {
            'old_password': self.default_password,
            'new_password': 'sup3rs4f3!!!',
            'new_password2': ''
        }
        resp = self.client.post(self.reverse(self.url_name), data)
        self.assert400(resp)

    def test_passwords_dont_match(self):
        self.login(self.user)
        data = {
            'old_password': self.default_password,
            'new_password': 'sup3rs4f3!!!',
            'new_password2': 'different'
        }
        resp = self.client.post(self.reverse(self.url_name), data)
        self.assert400(resp)

    def test_valid_password_change(self):
        self.login(self.user)
        data = {
            'old_password': self.default_password,
            'new_password': 'sup3rs4f3!!!',
            'new_password2': 'sup3rs4f3!!!'
        }
        resp = self.client.post(self.reverse(self.url_name), data)
        self.assert200(resp)


class ResetPasswordTestCase(BaseTestCase):
    url_name = 'shoutit_auth-reset-password'
    longMessage = True

    @classmethod
    def setUpTestData(cls):
        cls.user = cls.create_user()

    def test_unauth_no_data(self):
        resp = self.client.post(self.reverse(self.url_name))
        self.assert400(resp)

    def test_email_does_not_exist(self):
        data = {
            'email': 'email@doesnotexist.com'
        }
        resp = self.client.post(self.reverse(self.url_name), data)
        self.assert400(resp)

    def test_valid_password_reset(self):
        data = {
            'email': self.user.email
        }
        resp = self.client.post(self.reverse(self.url_name), data)
        self.assert200(resp)


class SetPasswordTestCase(BaseTestCase):
    url_name = 'shoutit_auth-set-password'
    longMessage = True

    @classmethod
    def setUpTestData(cls):
        cls.user = cls.create_user()
        cls.token = ConfirmToken.objects.create(user=cls.user, type=TOKEN_TYPE_RESET_PASSWORD)

    def test_unauth_no_data(self):
        resp = self.client.post(self.reverse(self.url_name))
        self.assert400(resp)

    def test_invalid_token(self):
        data = {
            'reset_token': 'invalid_token',
            'new_password': 'sup3rs4f3!!!',
            'new_password2': 'sup3rs4f3!!!',
        }
        resp = self.client.post(self.reverse(self.url_name), data)
        self.assert400(resp)

    def test_missing_password(self):
        data = {
            'reset_token': self.token.token,
            'new_password': 'sup3rs4f3!!!',
            'new_password2': ''
        }
        resp = self.client.post(self.reverse(self.url_name), data)
        self.assert400(resp)

    def test_passwords_dont_match(self):
        data = {
            'reset_token': self.token.token,
            'new_password': 'sup3rs4f3!!!',
            'new_password2': 'different'
        }
        resp = self.client.post(self.reverse(self.url_name), data)
        self.assert400(resp)

    def test_valid_password_update(self):
        data = {
            'reset_token': self.token.token,
            'new_password': 'sup3rs4f3!!!',
            'new_password2': 'sup3rs4f3!!!'
        }
        resp = self.client.post(self.reverse(self.url_name), data)
        self.assert200(resp)


class VerifyEmailTestCase(BaseTestCase):
    url_name = 'shoutit_auth-verify-email'
    longMessage = True

    @classmethod
    def setUpTestData(cls):
        cls.user = cls.create_user()
        cls.token = ConfirmToken.objects.create(user=cls.user, type=TOKEN_TYPE_EMAIL)

    def test_resend_unauth_no_data(self):
        resp = self.client.post(self.reverse(self.url_name))
        self.assert401(resp)

    def test_resend_email_does_not_exist(self):
        self.login(self.user)
        data = {
            'email': 'email@doesnotexist.com'
        }
        resp = self.client.post(self.reverse(self.url_name), data)
        # When a user is already verified, the validation is skipped and results in automatic success
        self.assert200(resp)

    def test_resend_email_valid_data(self):
        self.login(self.user)
        data = {
            'email': self.user.email
        }
        resp = self.client.post(self.reverse(self.url_name), data)
        self.assert200(resp)

    def test_verify_unauth_no_data(self):
        resp = self.client.get(self.reverse(self.url_name))
        self.assert400(resp)

    def test_verify_user_email(self):
        """
        Testing correct verification and follow up calls.
        """
        self.login(self.user)
        data = {
            'token': self.token.token
        }
        resp = self.client.get(self.reverse(self.url_name), data)
        self.assert200(resp)
        self.assertIn(
            'access_token',
            loads(resp.content).keys(),
            msg='When the verification was successful, the response should contain an access token'
        )

        self.user.refresh_from_db()
        self.assertTrue(
            self.user.is_activated,
            msg='After a successful call to the verification view the user should be active'
        )

        resp = self.client.get(self.reverse(self.url_name), data)
        self.assert400(resp)
        self.assertIn(
            'error',
            loads(resp.content).keys(),
            msg='When the verification view is called again, the response should contain an error'
        )

    def test_verify_invalid_token(self):
        self.login(self.user)
        data = {
            'token': 'invalidtoken'
        }
        resp = self.client.get(self.reverse(self.url_name), data)
        self.assert400(resp)
        self.assertIn(
            'error',
            loads(resp.content).keys(),
            msg='When the user is logged in but uses an invalid token, the result should be an error'
        )


class AccessTokenTestCase(BaseTestCase):
    longMessage = True
    url_name = 'access_token'
    default_data = {
        'client_id': 'shoutit-test',
        'client_secret': 'd89339adda874f02810efddd7427ebd6',
        'mixpanel_distinct_id': '67da5c7b-8312-4dc5-b7c2-f09b30aa7fa1',
    }

    @classmethod
    def setUpTestData(cls):
        cls.user = cls.create_user(email=cls.default_email)
        cls.user2 = cls.create_user(
            username='hans.zimmer',
            first_name='Hans',
            last_name='Zimmer',
            email='hans@example.com',
        )
        category = Category.objects.get(slug='services')
        cls.shout = cls.create_shout2(user=cls.user, shout_type=0, title='Pets Service 1', text='', price=None,
                                      currency=None, category=category, location=DEFAULT_LOCATION)

    def get_data(self, new_data=None):
        data = self.default_data.copy()
        if new_data is not None:
            data.update(new_data)
        return data

    def test_access_token_nodata(self):
        resp = self.client.post(self.reverse(self.url_name))
        self.assert400(resp)

    def test_login_google_code(self):
        return  # TODO I couldn't figure out right away how to setup the fixtures here
        # g_account = G(LinkedGoogleAccount, user=self.user)
        # data = self.get_data({
        #     "grant_type": "gplus_code",
        #     "gplus_code": g_account.gplus_id
        # })
        # resp = self.client.post(self.reverse(self.url_name), data)
        # self.assert200(resp)

    @responses.activate
    def test_login_facebook_code(self):
        data = self.get_data({
            "grant_type": "facebook_access_token",
            "facebook_access_token": "123"
        })

        expires_at = datetime.now() + timedelta(days=7)
        expires_at_ts = int(time.mktime(expires_at.timetuple()))

        facebook_response = {
            "id": "123456789097654",
            "email": "hans.zimmer@example.com",
            "name": "Hans Zimmer",
            "first_name": "Hans",
            "last_name": "Zimmer",
            "gender": "male",
            "picture": {
                "data": {
                    "height": 415,
                    "is_silhouette": "false",
                    "url": "https://scontent.xx.fbcdn.net/v/t1.0-1/10246800_1355580441027092_8676507526870221841_n.jpg?oh=555501ba29b829b89a5fbb4dfaad0091&oe=453300B1",
                    "width": 415
                }
            },
            "cover": {
                "id": "1562904555561383",
                "offset_y": 59,
                "source": "https://scontent.xx.fbcdn.net/t31.0-8/q82/s720x720/10555590_1562904180661383_5329368429206082288_o.jpg"
            }
        }

        facebook_debug = {
            'data': {
                "app_id": "1231231",
                "application": "some_test_app",
                "expires_at": expires_at_ts,
                "is_valid": True,
                "scopes": [
                    "user_birthday",
                    "email",
                    "public_profile"
                ],
                "user_id": "123456"
            }
        }

        facebook_access_token = {
            "access_token": "EAAEM8234sdf",
            "token_type": "bearer",
            "expires": 5183341
        }
        responses.add(responses.GET, 'https://graph.facebook.com/v2.6/me',
                      json=facebook_response, status=200)
        responses.add(responses.GET, 'https://graph.facebook.com/v2.6/debug_token',
                      json=facebook_debug, status=200)
        responses.add(responses.GET,
                      FB_GRAPH_ACCESS_TOKEN_URL,
                      json=facebook_access_token, status=200)
        resp = self.client.post(self.reverse(self.url_name), data)
        self.assert200(resp)

    def test_login_shoutit_account_wrong_password(self):
        data = self.get_data({
            'grant_type': 'shoutit_login',
            'email': self.default_email,
            'password': 'wrong'
        })
        resp = self.client.post(self.reverse(self.url_name), data)
        self.assert400(resp)

    def test_login_shoutit_account_wrong_email(self):
        data = self.get_data({
            'grant_type': 'shoutit_login',
            'email': 'wrongemail@example.com',
            'password': self.default_password
        })
        resp = self.client.post(self.reverse(self.url_name), data)
        self.assert400(resp)

    def test_login_shoutit_account(self):
        data = self.get_data({
            'grant_type': 'shoutit_login',
            'email': self.default_email,
            'password': self.default_password,
        })
        resp = self.client.post(self.reverse(self.url_name), data)
        self.assert200(resp)

    def test_create_shoutit_account_short_password(self):
        data = self.get_data({
            'grant_type': 'shoutit_signup',
            'name': self.default_first_name,
            'email': self.default_email,
            'password': '123'
        })
        resp = self.client.post(self.reverse(self.url_name), data)
        self.assert400(resp)

    def test_create_shoutit_account_email_exists(self):
        data = self.get_data({
            'grant_type': 'shoutit_signup',
            'name': self.default_first_name,
            'email': self.user2.email,
            'password': '123'
        })
        resp = self.client.post(self.reverse(self.url_name), data)
        self.assert400(resp)

    def test_create_shoutit_account_valid(self):
        """
        Testing signup with email and pw.
        """
        data = self.get_data({
            'grant_type': 'shoutit_signup',
            'name': 'Mike',
            'email': 'mike@example.com',
            'password': self.default_password,
            'profile': {
                'location': {
                    'latitude': 48.7533744,
                    'longitude': 11.3796516
                }
            },
        })
        user_count_pre = User.objects.count()
        profile_count_pre = Profile.objects.count()
        resp = self.client.post(self.reverse(self.url_name), data)
        self.assert200(resp)
        self.assertEqual(
            User.objects.count(), user_count_pre + 1, msg=(
                'After successful post for shoutit account creation, there should be one'
                ' extra User instance in the database.'
            )
        )
        self.assertEqual(
            Profile.objects.count(), profile_count_pre + 1, msg=(
                'After successful post for shoutit account creation, there should be one'
                ' Profile instance in the database.'
            )
        )

    def test_create_shoutit_page(self):
        page_category = G(PageCategory, slug='page-category-slug')

        data = self.get_data({
            'grant_type': 'shoutit_page',
            'page_category': {
                'slug': page_category.slug,
            },
            'page_name': 'Super Page',
            'name': self.default_first_name,
            'email': 'newaccount@example.com',
            'password': self.default_password,
        })
        user_count_pre = User.objects.count()
        profile_count_pre = User.objects.count()
        page_count_pre = Page.objects.count()
        resp = self.client.post(self.reverse(self.url_name), data)
        self.assert200(resp)
        self.assertEqual(
            User.objects.count(), user_count_pre + 2, msg=(
                'After successful post for shoutit account creation, there should be two'
                ' new User instances in the database.'
            )
        )
        self.assertEqual(
            Profile.objects.count(), profile_count_pre + 1, msg=(
                'After successful post for shoutit account creation, there should be one'
                ' Profile instance in the database.'
            )
        )
        self.assertEqual(
            Page.objects.count(), page_count_pre + 1, msg=(
                'After successful post for shoutit account creation, there should be one'
                ' Page instance in the database.'
            )
        )

    def test_create_shoutit_guest(self):
        data = self.get_data({
            'grant_type': 'shoutit_guest',
            'profile': {
                'location': {
                    'latitude': 48.7533744,
                    'longitude': 11.3796516
                },
                'push_tokens': {
                    'apns': 'APNS_PUSH_TOKEN',
                },
            },
        })
        user_count_pre = User.objects.count()
        resp = self.client.post(self.reverse(self.url_name), data)
        self.assert200(resp)
        self.assertEqual(
            User.objects.count(), user_count_pre + 1, msg=(
                'After successful post for shoutit account creation, there should be one'
                ' User instance in the database.'
            )
        )

    def test_auth_sms_code(self):
        dbclcon = G(
            DBCLConversation,
            from_user=self.user,
            to_user=self.user2,
            sms_code='123456',
            shout=self.shout,
        )
        data = self.get_data({
            'grant_type': 'sms_code',
            'sms_code': dbclcon.sms_code,
        })
        resp = self.client.post(self.reverse(self.url_name), data)
        self.assert200(resp)

    def test_auth_token(self):
        token = G(AuthToken, user=self.user)
        data = self.get_data({
            'grant_type': 'auth_token',
            'auth_token': token.id
        })
        resp = self.client.post(self.reverse(self.url_name), data)
        self.assert200(resp)

    def test_refresh_token(self):
        token = G(RefreshToken, user=self.user, client=Client.objects.get(client_id='shoutit-test'))
        data = self.get_data({
            'grant_type': 'refresh_token',
            'refresh_token': token.token
        })
        resp = self.client.post(self.reverse(self.url_name), data)
        self.assert200(resp)
