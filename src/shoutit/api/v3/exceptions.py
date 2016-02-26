# -*- coding: utf-8 -*-
"""

"""
from __future__ import unicode_literals

from rest_framework.exceptions import ValidationError

FB_LINK_ERROR_TRY_AGAIN = ValidationError({'error': "Could not link Facebook account, try again later."})
FB_LINK_ERROR_EMAIL = ValidationError({'error': "Could not access user email, make sure you allowed it."})
FB_LINK_ERROR_NO_LINK = ValidationError({'error': "No Facebook account to unlink."})

GPLUS_LINK_ERROR_TRY_AGAIN = ValidationError({'error': "Could not link G+ account, try again later."})
GPLUS_LINK_ERROR_EMAIL = ValidationError({'error': "Could not access user email, make sure you allowed it."})
GPLUS_LINK_ERROR_NO_LINK = ValidationError({'error': "No G+ account to unlink."})
