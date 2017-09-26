# -*- coding: utf-8 -*-
"""

"""
import uuid

from rest_framework.exceptions import ValidationError


class UUIDViewSetMixin(object):
    lookup_field = 'id'

    def get_object(self):
        value = self.kwargs.get(self.lookup_field)
        try:
            uuid.UUID(value)
        except:
            raise ValidationError({'detail': "'%s' is not a valid id" % value})

        return super(UUIDViewSetMixin, self).get_object()
