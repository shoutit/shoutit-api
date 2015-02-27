# -*- coding: utf-8 -*-
"""

"""
from __future__ import unicode_literals
from rest_framework.pagination import PaginationSerializer


class CustomPaginationSerializerMixin(object):

    def get_custom_pagination_serializer(self, page, custom_serializer_class, custom_results_field='results'):
        """
        Return a serializer instance to use with paginated data using the `custom_serializer_class` and `custom_results_field`.
        """
        class PaginationSerializerClass(PaginationSerializer):
            results_field = custom_results_field

        class SerializerClass(PaginationSerializerClass):
            class Meta:
                object_serializer_class = custom_serializer_class

        pagination_serializer_class = SerializerClass
        context = self.get_serializer_context()
        return pagination_serializer_class(instance=page, context=context)

