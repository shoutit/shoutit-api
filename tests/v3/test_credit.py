# -*- coding: utf-8 -*-
from django_dynamic_fixture import G

from shoutit_credit.models import CreditTransaction, CreditRule
from shoutit_credit.models.profile import CompleteProfile, InvitationCode
from tests.base import BaseTestCase


class CreditBaseTestCase(BaseTestCase):
    longMessage = True

    @classmethod
    def setUpTestData(cls):
        cls.user = cls.create_user()
        # cls.credit_rule = G(CompleteProfile)
        # cls.credit_transaction = G(CreditTransaction, user=cls.user, rule=cls.credit_rule)
        cls.invitation_code = G(InvitationCode, user=cls.user)


class CreditTransactionsTestCase(CreditBaseTestCase):
    url_name = 'credit-transactions'

    def test_no_auth(self):
        resp = self.client.get(self.reverse(self.url_name))
        self.assert401(resp)

    def _test_list_transactions(self):
        # TODO cannot manage to set up fixtures. Errors on shoutit_credit.models.base.CreditRule#display:49 even though using `CompleteProfile`
        self.login(self.user)
        resp = self.client.get(self.reverse(self.url_name))
        self.assert200(resp)
        self.assertEqual(
            len(self.decode_json(resp).get('results', [])), 1,
            msg='There should be one credit transaction in the results: {0}'.format(
                self.decode_json(resp)
            )
        )


class CreditInvitationCodeTestCase(CreditBaseTestCase):
    url_name = 'credit-invitation-code'

    def test_no_auth(self):
        resp = self.client.get(self.reverse(self.url_name))
        self.assert401(resp)

    def test_list_invitation_codes(self):
        self.login(self.user)
        resp = self.client.get(self.reverse(self.url_name))
        self.assert200(resp)
        self.assertIn(
            'code',
            self.decode_json(resp).keys(),
            msg='There should be a code in the response: {0}'.format(
                self.decode_json(resp)
            )
        )
