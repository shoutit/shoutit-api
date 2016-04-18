# -*- coding: utf-8 -*-
"""

"""
from __future__ import unicode_literals
from django.core.management.base import BaseCommand
from django.conf import settings
from elasticsearch import NotFoundError

import shoutit
from shoutit.models import Shout, GoogleLocation


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
            index_name = 'shoutit_api_%s_%s' % (settings.SHOUTIT_ENV, index[0])

        try:
            shoutit.ES.indices.delete(index_name)
            self.stdout.write("Successfully flushed '{}' index. Make sure to restart the server immediately".format(index_name))
            if index_name.endswith('shout'):
                Shout.objects.all().update(is_indexed=False)
            elif index_name.endswith('location'):
                GoogleLocation.objects.all().update(is_indexed=False)
        except NotFoundError as e:
            self.stderr.write("Failed to flush index '%s'" % index_name)
            self.stderr.write("Error: " + str(e))
