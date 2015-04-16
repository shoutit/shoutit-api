# -*- coding: utf-8 -*-
"""

"""
from __future__ import unicode_literals

from django.core.management.base import BaseCommand
from django.conf import settings


class Command(BaseCommand):
    help = 'Flush the entire ES Index.'

    def handle(self, *args, **options):
        index_name = settings.ENV
        settings.ES.indices.delete(index_name)

        self.stdout.write("Successfully flushed '{}' index. Make sure to restart the server immediately.".format(index_name))
