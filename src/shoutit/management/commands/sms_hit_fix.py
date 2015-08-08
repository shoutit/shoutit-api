# -*- coding: utf-8 -*-
"""

"""
from __future__ import unicode_literals
from django.core.management.base import BaseCommand
import re
from shoutit.models import SMSInvitation
import random
from shoutit.utils import has_unicode


class Command(BaseCommand):
    help = 'Send mass SMS invitations.'

    def add_arguments(self, parser):
        # Positional arguments
        parser.add_argument('--count', default=10, type=int)
        parser.add_argument('--status', default=1, type=int)
        parser.add_argument('--countries', default='AE,SA,OM,QA,KW,BH,EG,LB,JO', type=str)
        parser.add_argument('--dry', dest='dry', action='store_true')
        parser.set_defaults(dry=False)

    def handle(self, *args, **options):
        # get sms invitations
        count = options['count']
        status = options['status']
        countries = options['countries'].split(',')
        sms_invitations = SMSInvitation.objects.filter(status=status, country__in=countries)[:count]

        if options['dry']:
            self.stdout.write("Would have tried to fix %s sms invitations" % len(sms_invitations))
            return

        one_e = "Hi there!\n list your '%s...' and more for FREE on\nshoutit.com/app"
        two_e = "Someone might be interested in your '%s...'\nlist FREE ads on\nshoutit.com/app"
        cut_e = 35
        english_sms = [one_e, two_e]

        one_a = "اعلن عن '%s...'\nبسهولة\nshoutit.com/app"
        two_a = "اعرض '%s...'\nمجانا على\nshoutit.com/app"
        cut_a = 30
        arabic_sms = [one_a, two_a]

        sent = []
        for sms_invitation in sms_invitations:
            try:
                orig_message = sms_invitation.message
                ad_title = re.search("'(.*)\.\.\.'", orig_message).groups()[0]
                if has_unicode(ad_title):  # arabic
                    new_message = random.choice(arabic_sms) % ad_title
                else:  # english
                    new_message = random.choice(english_sms) % ad_title
                # sms_invitation.save(update_fields=['message'])
                self.stderr.write("SMS fixed: %s" % new_message.encode('utf8'))
            except Exception as e:
                self.stderr.write("Error fix: %s" % e)

        self.stdout.write("Successfully fix %s sms invitations" % len(sent))
