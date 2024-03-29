# -*- coding: utf-8 -*-
"""

"""
from django.core.management.base import BaseCommand
from django.conf import settings
from elasticsearch import NotFoundError

import shoutit
from shoutit.models import Shout, GoogleLocation, ShoutIndex, LocationIndex


class Command(BaseCommand):
    help = 'Flush the entire ES Index.'

    def add_arguments(self, parser):
        group = parser.add_mutually_exclusive_group(required=True)
        group.add_argument('--index', nargs=1, type=str)
        group.add_argument('--full_index', nargs=1, type=str)

    def handle(self, *args, **options):
        index = options.get('index')
        full_index = options.get('full_index')
        if full_index:
            index_name = full_index[0]
        else:
            index_name = f'{settings.ES_BASE_INDEX}_{index[0]}'

        try:
            shoutit.ES.indices.delete(index_name)
            if index_name.endswith('shout'):
                Shout.objects.all().update(is_indexed=False)
                ShoutIndex.init()
            elif index_name.endswith('location'):
                GoogleLocation.objects.all().update(is_indexed=False)
                LocationIndex.init()

        except NotFoundError as e:
            self.stderr.write("Failed to flush index '%s'" % index_name)
            self.stderr.write("Error: " + str(e))
        else:
            self.stdout.write("Successfully flushed '{}' index.".format(index_name))
