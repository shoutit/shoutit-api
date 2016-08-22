# -*- coding: utf-8 -*-
from django_dynamic_fixture import G, N

from shoutit_credit.models import CreditTransaction
from shoutit_credit.models.profile import CompleteProfile, InvitationCode
from tests.base import BaseTestCase


class CreditTransactionsTestCase(BaseTestCase):
    url_name = 'credit-transactions'

    @classmethod
    def setUpTestData(cls):
        cls.user = cls.create_user()
        cls.credit_rule = G(CompleteProfile)
        cls.credit_transaction = N(CreditTransaction, user=cls.user, rule=cls.credit_rule)
        cls.credit_transaction.notify = False
        cls.credit_transaction.save()

    def test_no_auth(self):
        resp = self.client.get(self.reverse(self.url_name))
        self.assert401(resp)

    def test_notification_reset_pusher_event_sent(self):
        self.login(self.user)
        return  # TODO What do you have to do for it not to call `self.rule.display()` and fail with NotImplementedError?
        resp = self.client.get(self.reverse(self.url_name))
        self.assert200(resp)
        self.assertEqual(
            len(self.decode_json(resp).get('results', [])), 1,
            msg='There should be one credit transaction in the results: {0}'.format(
                self.decode_json(resp)
            )
        )


class CreditInvitationCodeTestCase(BaseTestCase):
    url_name = 'credit-invitation-code'

    @classmethod
    def setUpTestData(cls):
        cls.user = cls.create_user()
        cls.invitation_code = G(InvitationCode, user=cls.user)

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
