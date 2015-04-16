# -*- coding: utf-8 -*-
"""

"""
from __future__ import unicode_literals

from django.core.management.base import BaseCommand
from shoutit.controllers.shout_controller import create_shout_index
from shoutit.models import Shout


class Command(BaseCommand):
    help = 'Index all shouts'

    def handle(self, *args, **options):

        for shout in Shout.objects.all():
            create_shout_index(shout)

        self.stdout.write('Successfully indexed all shouts')
