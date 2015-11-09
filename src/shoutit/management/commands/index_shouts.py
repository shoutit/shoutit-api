# -*- coding: utf-8 -*-
"""

"""
from __future__ import unicode_literals

from django.core.management.base import BaseCommand
from elasticsearch.helpers import streaming_bulk
from shoutit.controllers.shout_controller import shout_index_from_shout
from shoutit.models import Shout
from shoutit import ES


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
        shout_index_dicts = []
        for shout in Shout.objects.filter(is_disabled=False, muted=False)[_from:_to]:
            shout_index_dicts.append(shout_index_from_shout(shout).to_dict(True))
        for ok, info in streaming_bulk(ES, shout_index_dicts, chunk_size=1000):
            self.stdout.write("Created ShoutIndex: %s" % info['index']['_id'])
        self.stdout.write('Successfully indexed shouts from %s to %s' % (_from, _to))
