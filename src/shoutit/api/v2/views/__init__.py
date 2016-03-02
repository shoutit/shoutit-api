# -*- coding: utf-8 -*-
"""

"""
from __future__ import unicode_literals

from rest_framework.parsers import FormParser, MultiPartParser

from ...parsers import ShoutitJSONParser

DEFAULT_PARSER_CLASSES_v2 = (
    ShoutitJSONParser,
    FormParser,
    MultiPartParser
)
