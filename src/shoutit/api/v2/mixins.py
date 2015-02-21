# -*- coding: utf-8 -*-
"""

"""
from __future__ import unicode_literals


class CustomPaginationSerializerMixin(object):

    def get_custom_pagination_serializer(self, page, serializer_class):
        """
        Return a serializer instance to use with paginated data using the `serializer_class` param
        """
        class SerializerClass(self.pagination_serializer_class):
            class Meta:
                object_serializer_class = serializer_class

        pagination_serializer_class = SerializerClass
        context = self.get_serializer_context()
        return pagination_serializer_class(instance=page, context=context)

