# -*- coding: utf-8 -*-
"""

"""
from django.core.management.base import BaseCommand

from shoutit.controllers.email_controller import subscribe_users_to_mailing_list
from shoutit.models import User
from shoutit.utils import UserIds


class Command(BaseCommand):
    help = 'Subscribe users to mailing list'

    def add_arguments(self, parser):
        parser.add_argument('--limit', nargs=1, type=int, default=[3000])

    def handle(self, *args, **options):
        limit = options.get('limit')[0]
        max_emails = 1500
        user_ids = User.objects.exclude(email='', on_mailing_list=True)
        user_ids = list(user_ids.values_list('id', flat=True)[:limit])
        main_len = len(user_ids)

        while len(user_ids) > max_emails:
            chunk = user_ids[-max_emails:]
            user_ids = user_ids[:-max_emails]
            subscribe_users_to_mailing_list(user_ids=UserIds(chunk), raise_errors=False)
        subscribe_users_to_mailing_list(user_ids=UserIds(user_ids), raise_errors=False)

        self.stdout.write('Successfully created queues with %s users to be added to the mailing list' % main_len)
