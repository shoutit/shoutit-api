# -*- coding: utf-8 -*-
"""

"""
import uuid

from django.utils.translation import ugettext_lazy as _

from shoutit.api.v3.exceptions import ShoutitBadRequest, ERROR_REASON


class UUIDViewSetMixin(object):
    lookup_field = 'id'

    def get_object(self):
        value = self.kwargs.get(self.lookup_field)
        try:
            uuid.UUID(value)
        except ValueError:
            raise ShoutitBadRequest(message=_("Resource not found"), developer_message="'%s' is not a valid id" % value,
                                    reason=ERROR_REASON.INVALID_IDENTIFIER)

        return super(UUIDViewSetMixin, self).get_object()
