# -*- coding: utf-8 -*-
from tests.base import BaseTestCase


class NotificationsListTestCase(BaseTestCase):
    url_name = 'notification-list'

    def test_notifications_list_nodata(self):
        resp = self.client.get(self.reverse(self.url_name))
        self.assert401(resp)


class NotificationsReadTestCase(BaseTestCase):
    url_name = 'notification-read'

    def test_notifications_read_unknown(self):
        resp = self.client.get(self.reverse(self.url_name, kwargs={'id': 1}))
        self.assert401(resp)


class NotificationsResetTestCase(BaseTestCase):
    url_name = 'notification-reset'

    def test_notifications_reset_unknown(self):
        resp = self.client.get(self.reverse(self.url_name))
        self.assert401(resp)
