# -*- coding: utf-8 -*-
"""

"""
from django.core.management.base import BaseCommand

from shoutit.models import User
from shoutit.utils import UserIds
from shoutit.controllers.mixpanel_controller import add_to_mp_people, MAX_MP_BUFFER_SIZE


class Command(BaseCommand):
    help = 'Add profiles to MixPanel People'

    def add_arguments(self, parser):
        parser.add_argument('--limit', nargs=1, type=int, default=[3000])

    def handle(self, *args, **options):
        limit = options.get('limit')[0]
        max_users = MAX_MP_BUFFER_SIZE
        user_ids = User.objects.exclude(on_mp_people=True).exclude(accesstoken=None)
        user_ids = list(user_ids.values_list('id', flat=True)[:limit])
        main_len = len(user_ids)

        while len(user_ids) > max_users:
            chunk = user_ids[-max_users:]
            user_ids = user_ids[:-max_users]
            add_to_mp_people(user_ids=UserIds(chunk), buffered=True)
        add_to_mp_people(user_ids=UserIds(user_ids), buffered=True)

        self.stdout.write('Successfully created queues for %s profiles to be added to MixPanel People' % main_len)
