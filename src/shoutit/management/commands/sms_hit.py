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
from shoutit.utils import nexmo_client


class Command(BaseCommand):
    help = 'Send mass SMS invitations.'

    def add_arguments(self, parser):
        # Positional arguments
        parser.add_argument('--count', default=10, type=int)
        parser.add_argument('--countries', default='AE,SA,OM,QA,KW,BH,EG,LB,JO', type=str)

    def handle(self, *args, **options):
        # get sms invitations
        count = options['count']
        countries = options['countries'].split(',')
        sms_invitations = SMSInvitation.objects.filter(status=1, country__in=countries)[:count]

        sent = []
        for sms_invitation in sms_invitations:
            try:
                message = {
                    'from': 'Shoutit Adv',
                    'to': sms_invitation.mobile,
                    'type': 'unicode',
                    'text': sms_invitation.message
                }
                nexmo_client.send_message(message)
                sent.append(sms_invitation.pk)
                self.stderr.write("SMS sent: %s" % sms_invitation.mobile)
            except Exception as e:
                self.stderr.write("Error sending: %s" % e)

        SMSInvitation.objects.filter(id__in=sent).update(status=2)
        self.stdout.write("Successfully sent %s sms invitations" % len(sent))
