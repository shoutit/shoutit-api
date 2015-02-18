# -*- coding: utf-8 -*-
"""

"""
from __future__ import unicode_literals
from logging import Filter, WARNING


class LevelBelowWarning(Filter):
    def filter(self, record):
        return record.levelno < WARNING
