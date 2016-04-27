# -*- coding: utf-8 -*-
"""

"""
from __future__ import unicode_literals
from logging import Filter, WARNING
from django.conf import settings


class LevelBelowWarning(Filter):
    def filter(self, record):
        return record.levelno < WARNING


class UseSentry(Filter):
    def filter(self, record):
        return settings.USE_SENTRY
