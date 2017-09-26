# -*- coding: utf-8 -*-
"""

"""
from rest_framework.parsers import FormParser, MultiPartParser

from ...parsers import ShoutitJSONParser

DEFAULT_PARSER_CLASSES_v2 = (
    ShoutitJSONParser,
    FormParser,
    MultiPartParser
)
