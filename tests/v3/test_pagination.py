# -*- coding: utf-8 -*-
from django.test import override_settings
from django.core.urlresolvers import reverse
from rest_framework import viewsets, routers, permissions, serializers
from django_fake_model import models as f

from common.utils import date_unix
from shoutit.models.base import UUIDModel
from shoutit.api.v3 import pagination
from tests.base import BaseTestCase


class MyModel(UUIDModel, f.FakeModel):
    class Meta:
        app_label = 'django_fake_models'

    def __str__(self):
        return 'c: {}; m: {}'.format(self.created_at, self.modified_at)


class DateTimeSerializer(serializers.ModelSerializer):
    class Meta:
        model = MyModel


class BaseViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = (permissions.AllowAny, )
    queryset = MyModel.objects.all()
    serializer_class = DateTimeSerializer


class DateTimeViewSet(BaseViewSet):
    pagination_class = pagination.DateTimePagination


class ReverseDateTimeViewSet(BaseViewSet):
    pagination_class = pagination.ReverseDateTimePagination


class ReverseModifiedDateTimeViewSet(BaseViewSet):
    pagination_class = pagination.ReverseModifiedDateTimePagination


class Router(routers.DefaultRouter):
    include_format_suffixes = False

router = Router()
router.register('dt_created_asc', DateTimeViewSet, 'dt_created_asc')
router.register('dt_created_desc', ReverseDateTimeViewSet, 'dt_created_desc')
router.register('dt_modified_desc', ReverseModifiedDateTimeViewSet, 'dt_modified_desc')
urlpatterns = router.urls


@MyModel.fake_me
@override_settings(ROOT_URLCONF='tests.v3.test_pagination')
class PaginationTestCase(BaseTestCase):
    dt_created_asc_url = 'dt_created_asc-list'
    dt_created_desc_url = 'dt_created_desc-list'
    dt_modified_desc_url = 'dt_modified_desc-list'

    def setUp(self):
        m1 = MyModel.objects.create()
        self.update_auto_dt_field(m1, 'created_at', self.dt_before(days=4))
        self.update_auto_dt_field(m1, 'modified_at', self.dt_before(days=1))
        m2 = MyModel.objects.create()
        self.update_auto_dt_field(m2, 'created_at', self.dt_before(days=3))
        self.update_auto_dt_field(m2, 'modified_at', self.dt_before(days=2))
        m3 = MyModel.objects.create()
        self.update_auto_dt_field(m3, 'created_at', self.dt_before(days=2))
        self.update_auto_dt_field(m3, 'modified_at', self.dt_before(days=3))
        m4 = MyModel.objects.create()
        self.update_auto_dt_field(m4, 'created_at', self.dt_before(days=1))
        self.update_auto_dt_field(m4, 'modified_at', self.dt_before(days=4))

        self.mms = [m1, m2, m3, m4]

    def test_datetime_created_descending_after(self):
        after = date_unix(self.dt_before(days=2, hours=1))
        q_get = '?after={}'.format(after)
        resp = self.client.get(reverse(self.dt_created_desc_url) + q_get)
        self.assert200(resp)
        self.assert_ids_equal(self.get_results(resp), self.mms[2:][::-1], True)

    def test_datetime_created_descending_after_page_size(self):
        after = date_unix(self.dt_before(days=2, hours=1))
        q_get = '?after={}&page_size=1'.format(after)
        resp = self.client.get(reverse(self.dt_created_desc_url) + q_get)
        self.assert200(resp)
        self.assert_ids_equal(self.get_results(resp), self.mms[2:3], True)

    def test_datetime_created_descending_before(self):
        before = date_unix(self.dt_before(days=1, hours=1))
        q_get = '?before={}'.format(before)
        resp = self.client.get(reverse(self.dt_created_desc_url) + q_get)
        self.assert200(resp)
        self.assert_ids_equal(self.get_results(resp), self.mms[:3][::-1], True)

    def test_datetime_created_ascending_after(self):
        after = date_unix(self.dt_before(days=2, hours=1))
        q_get = '?after={}'.format(after)
        resp = self.client.get(reverse(self.dt_created_asc_url) + q_get)
        self.assert200(resp)
        self.assert_ids_equal(self.get_results(resp), self.mms[2:], True)

    def test_datetime_modified_descending_after(self):
        after = date_unix(self.dt_before(days=2, hours=1))
        q_get = '?after={}'.format(after)
        resp = self.client.get(reverse(self.dt_modified_desc_url) + q_get)
        self.assert200(resp)
        self.assert_ids_equal(self.get_results(resp), self.mms[:2], True)

    def get_results(self, resp):
        return self.decode_json(resp)['results']
