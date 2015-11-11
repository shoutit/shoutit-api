# -*- coding: utf-8 -*-
"""

"""
from __future__ import unicode_literals
from logging import Filter, WARNING
from django.conf import settings


class LevelBelowWarning(Filter):
    def filter(self, record):
        return record.levelno < WARNING


class OnServerOrForced(Filter):
    def filter(self, record):
        return settings.ON_SERVER or getattr(settings, 'FORCE_SENTRY', False)
