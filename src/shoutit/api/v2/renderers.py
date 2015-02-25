# -*- coding: utf-8 -*-
"""

"""
from __future__ import unicode_literals
from django.utils.encoding import smart_text
from rest_framework.renderers import BrowsableAPIRenderer
from rest_framework.utils import formatting


class ShoutitBrowsableAPIRenderer(BrowsableAPIRenderer):
    def get_context(self, data, accepted_media_type, renderer_context):
        context = super(ShoutitBrowsableAPIRenderer, self).get_context(data, accepted_media_type, renderer_context)
        context['display_edit_forms'] = False
        return context

    def get_description(self, view):
        try:
            description = getattr(view, view.action).__doc__ or ''
            description = formatting.dedent(smart_text(description)).split('---')
            description = description[0] if isinstance(description, list) else description
            return formatting.markup_description(description)
        except (AttributeError, TypeError):
            return super(ShoutitBrowsableAPIRenderer, self).get_description(view)
