# -*- coding: utf-8 -*-
"""

"""
from __future__ import unicode_literals
import datetime
from django.core.management.base import BaseCommand
from django.utils import timezone
from shoutit.controllers import message_controller
from shoutit.models import Conversation, DBCLConversation, SMSInvitation
import random
from shoutit.utils import nexmo_client, has_unicode


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
            self.stdout.write("Would have tried to send %s sms invitations" % len(sms_invitations))
            return

        sent = []
        for sms_invitation in sms_invitations:
            try:
                message = {
                    'from': 'Shoutit Adv',
                    'to': sms_invitation.mobile,
                    'text': sms_invitation.message,
                    'type': 'unicode' if has_unicode(sms_invitation.message) else None
                }
                nexmo_client.send_message(message)
                sent.append(sms_invitation.pk)
                self.stderr.write("SMS sent: %s" % sms_invitation.mobile)
            except Exception as e:
                self.stderr.write("Error sending: %s" % e)

        SMSInvitation.objects.filter(id__in=sent).update(status=2)
        self.stdout.write("Successfully sent %s sms invitations" % len(sent))
