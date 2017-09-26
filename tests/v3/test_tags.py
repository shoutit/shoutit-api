# -*- coding: utf-8 -*-
from unittest import skip

from django_dynamic_fixture import G

from common.constants import LISTEN_TYPE_TAG
from shoutit.models import FeaturedTag, Listen2, Tag
from shoutit.controllers.listen_controller import listen_to_object
from tests.base import BaseTestCase


class BaseTagsTestCase(BaseTestCase):
    longMessage = True

    @classmethod
    def setup_tag(cls):
        cls.tag = G(Tag, slug='foobar', name='Foobar')
        cls.featured = G(FeaturedTag, tag=cls.tag, title='Featured', rank=1)

    def get_tag_url(self):
        tag = getattr(self, 'tag', None)
        if tag is None:
            self.setup_tag()
            tag = self.tag
        return self.reverse(getattr(self, 'url_name', ''), kwargs={'slug': tag.slug})


class TagListTestCase(BaseTagsTestCase):
    url_name = 'tag-list'

    @classmethod
    def setUpTestData(cls):
        cls.setup_tag()

    def test_tag_list(self):
        resp = self.client.get(self.reverse(self.url_name))
        self.assert200(resp)
        self.assertEqual(
            len(self.decode_json(resp).get('results', [])),
            1,
            msg='There should be one Tag in the results.'
        )
        self.assertEqual(
            self.decode_json(resp).get('results')[0].get('id'),
            str(self.tag.id),
            msg='Result should contain the right tag.'
        )

    @skip('TODO Featured tags are deprecated in v3 and FeaturedTagSerializer breaks in this test')
    def test_featured_list(self):
        resp = self.client.get(self.reverse(self.url_name), data={'type': 'featured'})
        self.assert200(resp)
        self.assertEqual(
            len(self.decode_json(resp).get('results', [])),
            1,
            msg='There should be one Tag in the results.'
        )
        self.assertEqual(
            self.decode_json(resp).get('results')[0].get('id'),
            str(self.featured.id),
            msg='Result should contain the right tag.'
        )


class TagBatchListenTestCase(BaseTagsTestCase):
    url_name = 'tag-batch-listen'

    @classmethod
    def setUpTestData(cls):
        cls.user = cls.create_user()
        cls.setup_tag()

    def test_tag_batch_listen_unauth(self):
        resp = self.client.post(self.reverse(self.url_name))
        self.assert401(resp)
        resp = self.client.delete(self.reverse(self.url_name))
        self.assert401(resp)

    def test_batch_listen(self):
        self.login(self.user)
        data = {
            'tags': [
                {
                    'slug': self.tag.slug
                }
            ]
        }
        resp = self.client.post(self.reverse(self.url_name), data)
        self.assert202(resp)
        self.assertEqual(
            self.decode_json(resp).get('success', ''),
            'You started listening to shouts about {0}'.format(self.tag.name),
            msg='Should return the status of the listen.'
        )
        resp = self.client.delete(self.reverse(self.url_name), data)
        self.assert202(resp)
        self.assertEqual(
            self.decode_json(resp).get('success', ''),
            'You stopped listening to shouts about {0}'.format(self.tag.name),
            msg='Should return the status of the listen.'
        )


class TagDetailTestCase(BaseTagsTestCase):
    url_name = 'tag-detail'

    def test_tag_detail_unknown(self):
        resp = self.client.get(
            self.reverse(self.url_name, kwargs={'slug': 'unknown'}))
        self.assert404(resp)

    def test_detail(self):
        resp = self.client.get(self.get_tag_url())
        self.assert200(resp)
        self.assertEqual(
            self.decode_json(resp).get('id', ''),
            str(self.tag.id),
            msg='The tag should have been in the response.'
        )


class TagListenTestCase(BaseTagsTestCase):
    url_name = 'tag-listen'

    @classmethod
    def setUpTestData(cls):
        cls.user = cls.create_user()
        cls.setup_tag()

    def test_tag_listen_unauth(self):
        resp = self.client.post(self.get_tag_url())
        self.assert401(resp)
        resp = self.client.delete(self.get_tag_url())
        self.assert401(resp)

    def test_listen(self):
        self.login(self.user)
        resp = self.client.post(self.get_tag_url())
        self.assert202(resp)
        self.assertEqual(
            self.decode_json(resp).get('success', ''),
            'You started listening to shouts about {0}'.format(self.tag.name),
            msg='Should return the status of the listen.'
        )
        names = Listen2.objects.filter(user=self.user, type=LISTEN_TYPE_TAG).values_list('target', flat=True)
        self.assertIn(
            self.tag.name,
            names,
            msg="The tag name should be in the user's listens."
        )
        resp = self.client.delete(self.get_tag_url())
        self.assert202(resp)
        self.assertEqual(
            self.decode_json(resp).get('success', ''),
            'You stopped listening to shouts about {0}'.format(self.tag.name),
            msg='Should return the status of the listen.'
        )


class TagListenersTestCase(BaseTagsTestCase):
    url_name = 'tag-listeners'

    @classmethod
    def setUpTestData(cls):
        cls.setup_tag()
        cls.user = cls.create_user()
        listen_to_object(cls.user, cls.tag)

    def test_tag_listeners_unknown_unauth(self):
        resp = self.client.get(
            self.reverse(self.url_name, kwargs={'slug': 'unknown'}))
        self.assert404(resp)

    def test_listeners(self):
        resp = self.client.get(self.get_tag_url())
        self.assert200(resp)
        self.assertEqual(
            len(self.decode_json(resp).get('results', [])),
            1,
            msg='There should be one user in the results.'
        )
        self.assertEqual(
            self.decode_json(resp).get('results', [])[0].get('id'),
            str(self.user.id),
            msg='There should be the one listening user in the results.'
        )


class TagRelatedTestCase(BaseTagsTestCase):
    url_name = 'tag-related'

    @classmethod
    def setUpTestData(cls):
        cls.setup_tag()
        cls.tag2 = G(Tag, key=cls.tag.key, slug='barfoo', name='Barfoo')

    def test_tag_related_unknown_unauth(self):
        resp = self.client.get(
            self.reverse(self.url_name, kwargs={'slug': 'unknown'}))
        self.assert404(resp)

    def test_related(self):
        resp = self.client.get(self.get_tag_url())
        self.assert200(resp)
        self.assertEqual(
            len(self.decode_json(resp).get('results', [])),
            1,
            msg='There should be one related tag.'
        )
        self.assertEqual(
            self.decode_json(resp).get('results', [])[0].get('id'),
            str(self.tag2.id),
            msg='There should be the one related tag in the results.'
        )
