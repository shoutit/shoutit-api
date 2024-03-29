# -*- coding: utf-8 -*-
"""

"""
from django.utils.timezone import now

from common.constants import SMS_INVITATION_ADDED, SMS_INVITATION_QUEUED, SMS_INVITATION_SENT, SMS_INVITATION_ERROR
from django.core.management.base import BaseCommand
from shoutit.models import SMSInvitation
from shoutit.utils import nexmo_client, has_unicode


class Command(BaseCommand):
    help = 'Send mass SMS invitations.'

    def add_arguments(self, parser):
        parser.add_argument('--count', default=10, type=int)
        parser.add_argument('--status', default=SMS_INVITATION_ADDED, type=int)
        parser.add_argument('--countries', default='AE,SA,OM,QA,KW,BH,EG,LB,JO', type=str)
        parser.add_argument('--code', default='', type=str)
        parser.add_argument('--dry', dest='dry', action='store_true')
        parser.set_defaults(dry=False)

    def handle(self, *args, **options):
        count = options['count']
        status = options['status']
        code = options['code']
        countries = options['countries'].split(',')
        sms_invitations = SMSInvitation.objects.filter(status=status,
                                                       country__in=countries).order_by('modified_at')[:count]

        orig_app_link = 'shoutit.com/app'
        if code:
            if '%' in code:
                today = now()
                code = today.strftime(code)
            app_link = f'SHOUTIT.COM/app-{code}'
        else:
            app_link = orig_app_link
        self.stdout.write(f'APP Link: {app_link}')

        if options['dry']:
            self.stdout.write("Would have tried to send %s sms invitations" % len(sms_invitations))
            return

        all_ids = [s.id for s in sms_invitations]
        SMSInvitation.objects.filter(id__in=all_ids).update(status=SMS_INVITATION_QUEUED, modified_at=now())
        sent = []
        for sms_invitation in sms_invitations:
            try:
                text = sms_invitation.sent_text
                _has_unicode = has_unicode(text)
                if _has_unicode and len(text) > 70:
                    raise ValueError('max len 70 for unicode sms exceeded')
                if not _has_unicode and len(text) > 160:
                    raise ValueError('max len 160 for text sms exceeded')
                message = {
                    'from': 'Shoutit Adv',
                    'to': sms_invitation.mobile,
                    'text': text.replace(orig_app_link, app_link),
                    'type': 'unicode' if _has_unicode else None
                }
                res = nexmo_client.send_message(message)
                messages = res.get('messages')
                if messages and messages[0].get('status') == '9':
                    raise OverflowError
                sent.append(sms_invitation.id)
                self.stdout.write("SMS sent: %s" % sms_invitation.mobile)
            except OverflowError:
                self.stderr.write("Quota Exceeded, stopping...")
                break
            except Exception as e:
                self.stderr.write("Error sending: %s" % e)

        if sent:
            SMSInvitation.objects.filter(id__in=sent).update(status=SMS_INVITATION_SENT, modified_at=now())
            self.stdout.write("Successfully sent %s sms invitations" % len(sent))
        errors = list(set(all_ids) - set(sent))
        if errors:
            SMSInvitation.objects.filter(id__in=errors).update(status=SMS_INVITATION_ERROR, modified_at=now())
            self.stderr.write("Error sending %s sms invitations" % len(errors))

        self.stdout.write("Done")
