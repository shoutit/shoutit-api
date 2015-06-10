# -*- coding: utf-8 -*-
"""

"""
from __future__ import unicode_literals

from django.core.management.base import BaseCommand
from shoutit.controllers.shout_controller import save_shout_index
from shoutit.models import Shout


class Command(BaseCommand):
    help = 'Index all shouts'

    def add_arguments(self, parser):
        # Positional arguments
        parser.add_argument('from', nargs=1, type=int)
        parser.add_argument('to', nargs=1, type=int)

    def handle(self, *args, **options):
        # todo find better way to index all shouts no matter how many there is
        _from = options.get('from')[0]
        _to = options.get('to')[0]
        for shout in Shout.objects.filter(is_disabled=False, muted=False)[_from:_to]:
            save_shout_index(shout, delay=False)
        self.stdout.write('Successfully indexed shouts from %s to %s' % (_from, _to))
