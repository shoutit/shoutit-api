# -*- coding: utf-8 -*-
"""

"""
from __future__ import unicode_literals

from django.core.management.base import BaseCommand
from elasticsearch.helpers import bulk
from shoutit.models import GoogleLocation
from shoutit import ES
from shoutit.models.misc import location_index_from_location


class Command(BaseCommand):
    help = 'Index locations'

    def add_arguments(self, parser):
        parser.add_argument('--limit', nargs=1, type=int, default=[1000])

    def handle(self, *args, **options):
        limit = options.get('limit')[0]
        chunk = 500
        total_succeed = 0
        total_failed = 0
        for i in range(limit / chunk + (1 if limit % chunk > 0 else 0)):
            location_index_dicts = []
            locations = GoogleLocation.objects.filter(is_indexed=False)[:chunk if limit > chunk else limit]
            if not locations:
                break
            for location in locations:
                location_index_dicts.append(location_index_from_location(location).to_dict(True))
            succeed, errors = bulk(ES, location_index_dicts, chunk_size=250, raise_on_error=False, raise_on_exception=False)
            total_succeed += succeed
            failed = len(errors)
            total_failed += failed
            shout_ids = [x['_id'] for x in location_index_dicts]
            failed_ids = [x['index']['_id'] for x in errors]
            succeed_ids = set(shout_ids) - set(failed_ids)
            GoogleLocation.objects.filter(id__in=succeed_ids).update(is_indexed=True)
            self.stdout.write('-- Chunk %0.3d: Successfully indexed %s locations with %s errors' % (i + 1, succeed, failed))
        self.stdout.write('Successfully indexed %s locations with %s errors' % (total_succeed, total_failed))
