"""

"""
import json

from django.conf import settings
from django.utils import six
from rest_framework.exceptions import ParseError
from rest_framework.parsers import JSONParser


class ShoutitJSONParser(JSONParser):
    """
    Parses JSON-serialized data.
    """

    def parse(self, stream, media_type=None, parser_context=None):
        """
        Parses the incoming bytestream as JSON and returns the resulting data.
        Keeps the body accessible in `raw_body`
        """
        parser_context = parser_context or {}
        encoding = parser_context.get('encoding', settings.DEFAULT_CHARSET)

        try:
            raw_data = stream.read()
            stream.raw_body = raw_data
            data = raw_data.decode(encoding)
            return json.loads(data)
        except ValueError as exc:
            raise ParseError('JSON parse error - %s' % six.text_type(exc))
