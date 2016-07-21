"""

"""
from __future__ import unicode_literals

from rest_framework_extensions.key_constructor import bits
from rest_framework_extensions.key_constructor.constructors import KeyConstructor


class ShoutitDefaultCacheKeyConstructor(KeyConstructor):
    unique_method_id = bits.UniqueMethodIdKeyBit()
    format = bits.FormatKeyBit()
    language = bits.LanguageKeyBit()
    query_params = bits.QueryParamsKeyBit()


shoutit_default_cache_key_func = ShoutitDefaultCacheKeyConstructor()
