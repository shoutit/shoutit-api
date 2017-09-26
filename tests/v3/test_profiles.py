# -*- coding: utf-8 -*-
import time
from datetime import datetime, timedelta

from mock import patch
import responses
from django_dynamic_fixture import G, F
from django.contrib.auth import get_user_model
from django.test import override_settings
from push_notifications import apns

from shoutit.models import (
    Conversation, Video, Listen2, Tag, Message, LinkedFacebookAccount,
    ProfileContact, Page)
from shoutit.models.auth import APNSDevice, GCMDevice
from common.constants import (
    CONVERSATION_TYPE_CHAT, NOTIFICATION_TYPE_PROFILE_UPDATE,
    LISTEN_TYPE_PROFILE, LISTEN_TYPE_TAG
)
from tests.base import BaseTestCase, mocked_pusher


User = get_user_model()


class DetailMixin(object):

    @classmethod
    def get_url(cls, username):
        return cls.reverse(cls.url_name, kwargs={'username': username})


class ProfileListTestCase(BaseTestCase):
    url_name = 'profile-list'

    @classmethod
    def setUpTestData(cls):
        cls.user1 = cls.create_user(username='dima', email='dima@email.com',
                                    country='RU')
        cls.user2 = cls.create_user(username='john', email='john@email.com',
                                    country='US')

    def test_profile_list_anonymous(self):
        """
        Anonymous user can list profiles
        """
        resp = self.client.get(self.reverse(self.url_name))
        self.assert200(resp)
        self.assert_ids_equal(self.decode_json(resp)['results'],
                              [self.user1, self.user2])

    def test_profile_list_filter(self):
        """
        Profile list resource allows to filter data
        """
        resp = self.client.get(self.reverse(self.url_name) + '?country=ru')
        self.assert_ids_equal(self.decode_json(resp)['results'], [self.user1])

    def test_profile_list_search(self):
        """
        Profile list resource allows to search data
        """
        resp = self.client.get(self.reverse(self.url_name) + '?search=ima')
        self.assert_ids_equal(self.decode_json(resp)['results'], [self.user1])


class ProfileDetailTestCase(DetailMixin, BaseTestCase):
    url_name = 'profile-detail'

    @classmethod
    def setUpTestData(cls):
        cls.user1 = cls.create_user(username='dima', email='dima@email.com',
                                    country='RU')
        G(APNSDevice, user=cls.user1, registration_id='1')
        G(GCMDevice, user=cls.user1, registration_id='1')
        cls.user2 = cls.create_user(username='john', email='john@email.com')

    def test_profile_detail_unknown(self):
        """
        Resource returns 404 for not found username
        """
        resp = self.client.get(self.get_url('unknown'))
        self.assert404(resp)

    def test_profile_detail(self):
        """
        Anonymous user can get profile details for given username
        """
        resp = self.client.get(self.get_url(self.user1.username))
        self.assert200(resp)
        self.assert_ids_equal(self.decode_json(resp), self.user1)

    def test_profile_guest_detail(self):
        """
        Anonymous user can get profile details about guest user
        """
        User.objects.filter(id=self.user2.id).update(is_guest=True)
        resp = self.client.get(self.get_url(self.user2.username))
        self.assert200(resp)
        self.assertIn('date_joined', self.decode_json(resp))

    def test_profile_me_detail(self):
        """
        Logged-in user can view his own profile by 'me' username
        """
        self.login(self.user1)
        resp = self.client.get(self.get_url('me'))
        self.assert_ids_equal(self.decode_json(resp), self.user1)

    def test_profile_detail_with_conversation(self):
        """
        Conversation with requested profile is shown, if exists
        """
        conv = G(Conversation, type=CONVERSATION_TYPE_CHAT,
                 users=[self.user1, self.user2])
        self.login(self.user1)
        resp = self.client.get(self.get_url(self.user2.username))
        self.assert_ids_equal(self.decode_json(resp)['conversation'], conv)

    def test_profile_update_forbidden_to_another_user(self):
        """
        Logged-in user can't modify not his own profile
        """
        self.login(self.user1)
        resp = self.client.patch(self.get_url(self.user2.username),
                                 {'email': 'vasya@email.com'})
        self.assert403(resp)

    def test_profile_update_success(self):
        """
        User can update his own profile
        """
        self.login(self.user1)
        resp = self.client.patch(self.get_url(self.user1.username), {
            'email': 'vasya@email.com',
            'username': 'pasha',
            'first_name': 'Pavel',
            'last_name': 'Dudik',
        })
        self.assert200(resp)
        self.assertEqual(User.objects.get(id=self.user1.id).email,
                         'vasya@email.com')

    def test_profile_update_email_already_exists(self):
        """
        User can update his own profile
        """
        self.login(self.user1)
        resp = self.client.patch(self.get_url(self.user1.username),
                                 {'email': self.user2.email})
        self.assert400(resp)

    def test_profile_update_with_video(self):
        """
        Given video data is saved in user's profile
        """
        self.login(self.user1)
        video = self.get_video_data()
        resp = self.client.patch(self.get_url(self.user1.username),
                                 {'video': video})
        self.assert200(resp)
        self.assertEqual(User.objects.get(id=self.user1.id).profile.video.url,
                         video['url'])

    def test_profile_update_website_without_protocol(self):
        """
        Website without protocol is allowed to be saved in profile
        """
        self.login(self.user1)
        resp = self.client.patch(self.get_url(self.user1.username),
                                 {'website': 'ya.ru'})
        self.assert200(resp)
        self.assertEqual(User.objects.get(id=self.user1.id).profile.website,
                         'http://ya.ru')

    def test_profile_update_mobile(self):
        """
        Mobile phone number is saved in profile
        """
        self.login(self.user1)
        resp = self.client.patch(self.get_url(self.user1.username),
                                 {'mobile': '8 926 123-45-67'})
        self.assert200(resp)
        saved_mobile = User.objects.get(id=self.user1.id).profile.mobile
        self.assertTrue(saved_mobile.endswith('9261234567'))

    def test_profile_update_location(self):
        """
        City updated and is taken from given location
        """
        self._check_profile_location(self.user1)

    def test_guest_profile_update_location(self):
        """
        City updated and is taken from given location for guest user
        """
        User.objects.filter(id=self.user2.id).update(is_guest=True)
        self._check_profile_location(self.user2)

    def test_profile_delete_existing_video_data(self):
        """
        When video is updated as null, existing video is deleted
        """
        profile = self.user1.profile
        profile.video = G(Video, **self.get_video_data())
        profile.save()
        self.login(self.user1)
        resp = self.client.patch(self.get_url(self.user1.username),
                                 {'video': None})
        self.assert200(resp)
        user = User.objects.get(id=self.user1.id)
        self.assertTrue(user.profile.video is None)

    def test_profile_update_apns_tokens(self):
        """
        Provided apns token replace existing ones
        """
        self._check_profile_update_apns_tokens(self.user1)

    def test_guest_profile_update_apns_tokens(self):
        """
        Provided apns token replace existing ones for guest user
        """
        User.objects.filter(id=self.user2.id).update(is_guest=True)
        self._check_profile_update_apns_tokens(self.user2)

    def test_profile_update_gcm_tokens(self):
        """
        Provided apns token replace existing ones
        """
        self.login(self.user1)
        resp = self.client.patch(self.get_url(self.user1.username), {
            'push_tokens': {'gcm': '3'}
        })
        self.assert200(resp)
        apns_devices = GCMDevice.objects.filter(user=self.user1)
        self.assertEqual(
            [str(v) for v in apns_devices.values_list('registration_id', flat=True)],
            ['3'])

    @patch.object(mocked_pusher, 'trigger')
    def test_profile_update_pusher_event(self, m_trigger):
        """
        On user update request, 'profile update' pusher event is sent
        """
        self.login(self.user1)
        m_trigger.reset_mock()
        self.client.patch(self.get_url(self.user1.username), {
            'first_name': 'Pavel',
        })
        self.assert_pusher_event(
            m_trigger, str(NOTIFICATION_TYPE_PROFILE_UPDATE),
            channel_name=self.get_pusher_user_channel_name(self.user1.id),
            attached_object_partial_dict={'id': str(self.user1.id)})

    def test_test_user_destory(self):
        """
        Test user can delete himself
        """
        self.login(self.user1)
        resp = self.client.delete(self.get_url(self.user1.username))
        self.assert204(resp)
        self.assertFalse(User.objects.filter(id=self.user1.id).exists())

    def test_nontest_user_destroy(self):
        """
        Non-test user delete is not allowed currently
        """
        User.objects.filter(id=self.user1.id).update(is_test=False)
        self.login(self.user1)
        resp = self.client.delete(self.get_url(self.user1.username))
        self.assert406(resp)

    @responses.activate
    def _check_profile_location(self, user):
        self.add_googleapis_geocode_response('us_new_york.json')
        self.login(user)
        resp = self.client.patch(self.get_url(user.username),
                                 {'location': self.COORDINATES['USA']})
        self.assert200(resp)
        user = User.objects.get(id=user.id)
        self.assertEqual(user.profile.location['city'], 'New York')

    def _check_profile_update_apns_tokens(self, user):
        self.login(user)
        resp = self.client.patch(self.get_url(user.username), {
            'push_tokens': {'apns': '3'}
        })
        self.assert200(resp)
        apns_devices = APNSDevice.objects.filter(user=user)
        self.assertEqual(
            [str(v) for v in apns_devices.values_list('registration_id', flat=True)],
            ['3'])


class ProfileListenTestCase(DetailMixin, BaseTestCase):
    url_name = 'profile-listen'

    @classmethod
    def setUpTestData(cls):
        cls.user1 = cls.create_user(username='dima', email='dima@email.com',
                                    country='RU')
        cls.apns_device = G(APNSDevice, user=cls.user1)
        cls.user2 = cls.create_user(username='john', email='john@email.com')

    def test_profile_listen_unknown(self):
        resp = self.client.post(self.get_url('unknown'))
        self.assert401(resp)

    def test_user_cant_listen_for_himself(self):
        """
        User can't listen for himself
        """
        self.login(self.user1)
        resp = self.client.post(self.get_url(self.user1.username))
        self.assert400(resp)

    def test_user_listen_for_another_user(self):
        """
        User can listen to another user
        """
        self.login(self.user2)
        resp = self.client.post(self.get_url(self.user1.username))
        self.assert202(resp)
        self.assertEqual(self.user2.listen2s.first().target,
                         str(self.user1.id))

    @override_settings(USE_PUSH=True)
    @patch.object(apns, 'apns_send_bulk_message')
    def test_user_listen_push_event_apns(self, m_apns_bulk):
        """
        On listen request, 'listen' push event is sent to apns device
        """
        self.login(self.user2)
        self.client.post(self.get_url(self.user1.username))
        self.assert_ios_badge_set(
            m_apns_bulk, [self.apns_device.registration_id], badge=1)

    def test_user_stop_listen_another_user(self):
        """
        User stop listening another user
        """
        listen = G(Listen2, user=self.user2, type=int(LISTEN_TYPE_PROFILE),
                   target=self.user1.id)
        self.login(self.user2)
        resp = self.client.delete(self.get_url(self.user1.username))
        self.assert202(resp)
        self.assertFalse(Listen2.objects.filter(id=listen.id).exists())


class ProfileListenersTestCase(DetailMixin, BaseTestCase):
    url_name = 'profile-listeners'

    @classmethod
    def setUpTestData(cls):
        cls.user1 = cls.create_user(username='dima', email='dima@email.com')
        cls.user2 = cls.create_user(username='john', email='john@email.com')
        G(Listen2, user=cls.user2, type=int(LISTEN_TYPE_PROFILE),
          target=cls.user1.id)

    def test_profile_listeners_unknown(self):
        resp = self.client.get(self.get_url('unknown'))
        self.assert404(resp)

    def test_profile_listeners(self):
        """
        Response contains profiles, that are listening to current profile
        """
        self.login(self.user1)
        resp = self.client.get(self.get_url(self.user1.username))
        self.assert200(resp)
        self.assert_ids_equal(self.decode_json(resp)['results'],
                              [self.user2])


class ProfileListeningTestCase(DetailMixin, BaseTestCase):
    url_name = 'profile-listening'

    @classmethod
    def setUpTestData(cls):
        cls.user1 = cls.create_user(username='dima', email='dima@email.com')
        cls.user2 = cls.create_user(username='john', email='john@email.com')
        G(Listen2, user=cls.user1, type=int(LISTEN_TYPE_PROFILE),
          target=cls.user2.id)

    def test_profile_listeners_unknown(self):
        resp = self.client.get(self.get_url('unknown'))
        self.assert404(resp)

    def test_profile_listening(self):
        """
        Response contains profiles, that current profile is listening to
        """
        self.login(self.user1)
        resp = self.client.get(self.get_url(self.user1.username))
        self.assert200(resp)
        self.assert_ids_equal(self.decode_json(resp)['results'],
                              [self.user2])


class ProfileInterestTestCase(DetailMixin, BaseTestCase):
    url_name = 'profile-interests'

    @classmethod
    def setUpTestData(cls):
        cls.user1 = cls.create_user(username='dima', email='dima@email.com')
        cls.tag1 = G(Tag, name='bicycle', slug='bicycle')
        G(Listen2, user=cls.user1, type=int(LISTEN_TYPE_TAG),
          target=cls.tag1.name)

    def test_profile_interests_unknown(self):
        resp = self.client.get(self.get_url('unknown'))
        self.assert404(resp)

    def test_profile_interests(self):
        """
        Response contains tags, that current profile is listening to
        """
        self.login(self.user1)
        resp = self.client.get(self.get_url(self.user1.username))
        self.assert200(resp)
        self.assert_ids_equal(self.decode_json(resp)['results'],
                              [self.tag1])


class ProfileHomeTestCase(DetailMixin, BaseTestCase):
    url_name = 'profile-home'

    @classmethod
    def setUpTestData(cls):
        cls.delete_elasticsearch_index(index='*')
        cls.user1 = cls.create_user(username='dima', email='dima@email.com',
                                    country='RU')
        cls.user2 = cls.create_user(username='john', email='john@email.com')
        cls.shout1 = cls.create_shout(
            user=cls.user1, category=F(name='velo', slug='velo'), item=F(name='Marin'))

        cls.tag1 = G(Tag, name='bicycle', slug='bicycle', key=F(name='filter1', slug='filter1'))
        cls.tag2 = G(Tag, name='avto', slug='avto', key=F(name='filter2', slug='filter2'))
        # shout2 is tagged by tag1 and in same country as user1
        cls.shout2 = cls.create_shout(
            user=cls.user2, category=cls.shout1.category,
            item=F(name='Specialized AWOL'), country='RU')
        cls.shout2.tags.add(cls.tag1)
        cls.shout2.save()  # this makes sure the shout index is updated with the added tags
        # shout3 is tagged by tag2 and in same different as user1
        cls.shout3 = cls.create_shout(
            user=cls.user2, category=cls.shout1.category,
            item=F(name='Reno'), country='US')
        cls.shout3.tags.add(cls.tag2)
        cls.shout3.save()
        cls.refresh_elasticsearch_index(index='*')

    def test_profile_home_unknown(self):
        resp = self.client.get(self.get_url('unknown'))
        self.assert401(resp)

    def test_profile_cant_see_other_profile_home(self):
        """
        Looking to other profile's home is forbidden
        """
        self.login(self.user2)
        resp = self.client.get(self.get_url(self.user1.username))
        self.assert403(resp)

    def test_profile_home_users_shouts(self):
        """
        Resourse returns all user's shouts
        """
        self.login(self.user1)
        resp = self.client.get(self.get_url(self.user1.username))
        self.assert200(resp)
        self.assert_ids_equal(self.decode_json(resp)['results'],
                              [self.shout1])

    def test_profile_home_shouts_include_tag_same_country(self):
        """
        Resourse returns all user's shouts and tagged shouts for tags,
        that user is listening to. Tagged shouts and user are in same country.
        """
        # user1 is listening to tag1
        G(Listen2, user=self.user1, type=int(LISTEN_TYPE_TAG),
          target=self.tag1.name)
        self.login(self.user1)
        resp = self.client.get(self.get_url(self.user1.username))
        self.assert200(resp)
        self.assert_ids_equal(self.decode_json(resp)['results'],
                              [self.shout1, self.shout2])

    def test_profile_home_shouts_include_tag_other_country(self):
        """
        Resourse returns only user's shouts. In spite of user is listening
        to tag, shout with that tag is not listed, as it belongs to another
        country.
        """
        # user1 is listening to tag2
        G(Listen2, user=self.user1, type=int(LISTEN_TYPE_TAG),
          target=self.tag2.name)
        self.login(self.user1)
        resp = self.client.get(self.get_url(self.user1.username))
        self.assert200(resp)
        self.assert_ids_equal(self.decode_json(resp)['results'],
                              [self.shout1])


class ProfileChatTestCase(DetailMixin, BaseTestCase):
    url_name = 'profile-chat'

    @classmethod
    def setUpTestData(cls):
        cls.user1 = cls.create_user(username='dima', email='dima@email.com')
        cls.user2 = cls.create_user(username='john', email='john@email.com')
        G(Listen2, user=cls.user1, type=int(LISTEN_TYPE_PROFILE),
          target=cls.user2.id)
        cls.valid_msg = {'text': 'Message text'}

    def test_profile_chat_unknown(self):
        resp = self.client.post(self.get_url('unknown'), self.valid_msg)
        self.assert401(resp)

    def test_profile_cant_start_chat_with_himself(self):
        """
        User can't start chat with himself
        """
        self.login(self.user1)
        resp = self.client.post(self.get_url(self.user1.username),
                                self.valid_msg)
        self.assert400(resp)

    def test_profile_cant_chat_with_no_listener(self):
        """
        User can't start chat with non-listener
        """
        self.login(self.user1)
        resp = self.client.post(self.get_url(self.user2.username),
                                self.valid_msg)
        self.assert400(resp)

    def test_profile_send_message_to_chat(self):
        """
        User can start the chat with his listener
        """
        self.login(self.user2)
        resp = self.client.post(self.get_url(self.user1.username),
                                self.valid_msg)
        self.assert201(resp)
        messages = Message.objects.filter(text=self.valid_msg['text'])
        self.assertEqual(messages.count(), 1)
        conversation = messages.first().conversation
        self.assertEqual(conversation.creator, self.user2)
        self.assertIn(self.user1, conversation.users.all())
        self.assertIn(self.user2, conversation.users.all())


class ProfileLinkTestCase(DetailMixin, BaseTestCase):
    url_name = 'profile-link'
    expires_at = datetime.now() + timedelta(days=7)
    expires_at_ts = int(time.mktime(expires_at.timetuple()))

    facebook_response = {
        "id": "123456",
        "email": "user1@mail.com",
        "name": "Dima Goshev",
        "first_name": "Dima",
        "last_name": "Goshev",
        "gender": "male",
        "picture": {
            "data": {
                "height": 652,
                "is_silhouette": False,
                "url": "https://scontent.xx.fbcdn.net/v/123.jpg",
                "width": 631
            }
        },
        "cover": {
            "id": "78900234",
            "offset_y": 100,
            "source": "https://scontent.xx.fbcdn.net/567.jpg"
        },
        "friends": {
            "data": [],
            "summary": {
                "total_count": 39
            }
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

    # fb_exchange_token requests return `expires` unlike other Facebook access token requests which return `expires_in`
    facebook_access_token = {
        "access_token": "EAAEM8234sdf",
        "token_type": "bearer",
        "expires": 5183341
    }

    @classmethod
    def setUpTestData(cls):
        cls.user1 = cls.create_user(username='dima', email='dima@email.com')

    def test_profile_link_unknown(self):
        resp = self.client.patch(self.get_url('unknown'))
        self.assert401(resp)

    @responses.activate
    def test_profile_link_facebook(self):
        """
        Link facebook to current profile
        """
        responses.add(responses.GET, 'https://graph.facebook.com/v2.6/me',
                      json=self.facebook_response, status=200)
        responses.add(responses.GET, 'https://graph.facebook.com/v2.6/debug_token',
                      json=self.facebook_debug, status=200)
        responses.add(responses.GET,
                      'https://graph.facebook.com/oauth/access_token',
                      json=self.facebook_access_token, status=200)
        responses.add(responses.GET,
                      self.facebook_response['picture']['data']['url'],
                      body=self.get_1pixel_jpg_image_data(), status=200)
        responses.add(responses.GET,
                      self.facebook_response['cover']['source'],
                      body=self.get_1pixel_jpg_image_data(), status=200)

        self.login(self.user1)
        resp = self.client.patch(self.get_url(self.user1.username), {
            'account': 'facebook',
            'facebook_access_token': '123'
        })
        self.assert200(resp)
        self.assertEqual(self.user1.linked_facebook.facebook_id,
                         self.facebook_response['id'])

    def test_profile_unlink_facebook(self):
        """
        Unlink facebook from current profile
        """
        la = G(LinkedFacebookAccount, user=self.user1)
        self.login(self.user1)
        resp = self.client.delete(self.get_url(self.user1.username), {
            'account': 'facebook',
        })
        self.assert200(resp)
        self.assertFalse(LinkedFacebookAccount.objects.filter(id=la.id)
                         .exists())


class ProfileMutualFriendsTestCase(DetailMixin, BaseTestCase):
    url_name = 'profile-mutual-friends'

    @classmethod
    def setUpTestData(cls):
        cls.user1 = cls.create_user(username='dima', email='dima@email.com')
        G(LinkedFacebookAccount, user=cls.user1, facebook_id='1',
          friends=['2'])
        cls.user2 = cls.create_user(username='john', email='john@email.com')
        G(LinkedFacebookAccount, user=cls.user2, facebook_id='2',
          friends=['1'])

    def test_profile_mutual_friends_unknown(self):
        resp = self.client.get(self.get_url('unknown'))
        self.assert404(resp)

    def test_profile_mutual_friends(self):
        """
        Resource returns all facebook friends
        """
        self.login(self.user1)
        resp = self.client.get(self.get_url(self.user1.username))
        self.assert200(resp)
        self.assert_ids_equal(self.decode_json(resp)['results'], [self.user2])


class ProfileContactsTestCase(DetailMixin, BaseTestCase):
    url_name = 'profile-contacts'

    @classmethod
    def setUpTestData(cls):
        cls.user1 = cls.create_user(username='dima', email='dima@email.com')
        cls.valid_data = {
            'contacts': [
                {
                    "first_name": "John",
                    "last_name": "Doe",
                    "name": "",
                    "mobiles": ["+491501234567", "01501234567"],
                    "emails": ["john@example.com", "superman@andromeda.com"]
                },
                {
                    "first_name": "",
                    "last_name": "",
                    "name": "Sam Doe",
                    "mobiles": ["+96170364170"],
                    "emails": []
                }
            ]
        }

    def test_profile_contacts_unknown(self):
        resp = self.client.patch(self.get_url('unknown'), self.valid_data)
        self.assert401(resp)

    def test_profile_contacts_updated(self):
        """
        Provided contacts are saved for current user
        """
        self.login(self.user1)
        resp = self.client.patch(self.get_url(self.user1.username),
                                 self.valid_data)
        self.assert200(resp)
        contact1 = self.user1.contacts.filter(first_name='John')
        contact2 = self.user1.contacts.exclude(first_name='John')
        self.assertEqual(contact1.count(), 1)
        self.assertEqual(contact2.count(), 1)
        self.assertEqual(contact1.first().emails,
                         ["john@example.com", "superman@andromeda.com"])
        self.assertEqual(contact2.first().mobiles, ['+96170364170'])


class ProfileMutualContactsTestCase(DetailMixin, BaseTestCase):
    url_name = 'profile-mutual-contacts'

    @classmethod
    def setUpTestData(cls):
        cls.user1 = cls.create_user(username='dima', email='dima@email.com')
        cls.user2 = cls.create_user(username='john', email='john@email.com')
        G(ProfileContact, user=cls.user1, emails=['john@email.com'])

    def test_profile_mutual_contacts_unknown(self):
        resp = self.client.get(self.get_url('unknown'))
        self.assert404(resp)

    def test_profile_mutual_contacts(self):
        """
        Resource returns users, that are listed in current user contacts
        """
        self.login(self.user1)
        resp = self.client.get(self.get_url(self.user1.username))
        self.assert200(resp)
        self.assert_ids_equal(self.decode_json(resp)['results'], [self.user2])


class ProfileDeactivateTestCase(DetailMixin, BaseTestCase):
    url_name = 'profile-deactivate'

    @classmethod
    def setUpTestData(cls):
        cls.user1 = cls.create_user(username='dima', email='dima@email.com')
        cls.valid_data = {'password': cls.default_password}

    def test_profile_deactivate_unknown(self):
        resp = self.client.post(self.get_url('unknown'), self.valid_data)
        self.assert401(resp)

    def test_profile_deactivate(self):
        """
        Profile is deactivated successfully
        """
        self.login(self.user1)
        resp = self.client.post(self.get_url(self.user1.username),
                                self.valid_data)
        self.assert204(resp)
        self.assertFalse(User.objects.get(id=self.user1.id).is_active)

    def test_profile_deactivate_bad_password(self):
        """
        Profile is not deactivated due to bad password
        """
        self.login(self.user1)
        resp = self.client.post(self.get_url(self.user1.username),
                                {'password': 'bad'})
        self.assert400(resp)


class ProfilePagesTestCase(DetailMixin, BaseTestCase):
    url_name = 'profile-pages'

    @classmethod
    def setUpTestData(cls):
        cls.user1 = cls.create_user(username='dima', email='dima@email.com')
        cls.page1 = G(Page, user=cls.user1, creator=cls.user1, name='page1', slug='page1',
                      category=F(name='pagecat', slug='pagecat'))

    def test_profile_pages(self):
        """
        Resource return user's pages
        """
        resp = self.client.get(self.get_url(self.user1.username))
        self.assert200(resp)
        self.assert_ids_equal(self.decode_json(resp)['results'], [self.page1])
