# -*- coding: utf-8 -*-
from unittest import skip

from tests.base import BaseTestCase


class MiscCitiesTestCase(BaseTestCase):
    url_name = 'misc-cities'

    def test_mics_cities(self):
        resp = self.client.get(self.reverse(self.url_name))
        self.assert200(resp)


class MiscCurrenciesTestCase(BaseTestCase):
    url_name = 'misc-currencies'

    def test_mics_currencies(self):
        resp = self.client.get(self.reverse(self.url_name))
        self.assert200(resp)


class MiscErrorTestCase(BaseTestCase):
    url_name = 'misc-error'

    @skip("TODO: raises TypeError")
    def test_mics_error(self):
        resp = self.client.get(self.reverse(self.url_name))
        self.assert200(resp)


class MiscFBDeauthTestCase(BaseTestCase):
    url_name = 'misc-fb-deauth'

    def test_mics_fb_deauth_nodata(self):
        resp = self.client.post(self.reverse(self.url_name))
        self.assert200(resp)


class MiscFBScopesChangedTestCase(BaseTestCase):
    url_name = 'misc-fb-scopes-changed'

    def test_mics_fb_scopes_changed_nodata(self):
        resp = self.client.get(self.reverse(self.url_name))
        self.assert200(resp)


class MiscGeocodeTestCase(BaseTestCase):
    url_name = 'misc-geocode'

    def test_mics_geocode_nodata(self):
        resp = self.client.get(self.reverse(self.url_name))
        self.assert400(resp)


class MiscIpTestCase(BaseTestCase):
    url_name = 'misc-ip'

    def test_mics_ip_nodata(self):
        resp = self.client.get(self.reverse(self.url_name))
        self.assert200(resp)


class MiscReportsTestCase(BaseTestCase):
    url_name = 'misc-reports'

    def test_mics_reports_nodata(self):
        resp = self.client.post(self.reverse(self.url_name))
        self.assert401(resp)


class MiscSuggestionsTestCase(BaseTestCase):
    url_name = 'misc-suggestions'

    def test_mics_suggestions_nodata(self):
        resp = self.client.get(self.reverse(self.url_name))
        self.assert200(resp)
