# -*- coding: utf-8 -*-
"""

"""
from __future__ import unicode_literals

from django.core.management.base import BaseCommand
from shoutit.controllers.shout_controller import create_trade_index
from shoutit.models import *


class Command(BaseCommand):
    help = 'Index all shouts'

    def handle(self, *args, **options):

        for trade in Trade.objects.all():
            create_trade_index(trade)

        self.stdout.write('Successfully indexed all shouts')
