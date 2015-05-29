# -*- coding: utf-8 -*-
"""

"""
from __future__ import unicode_literals
from pusher import Pusher
from .settings import SHOUTIT_PUSHER_SETTINGS


pusher = Pusher(**SHOUTIT_PUSHER_SETTINGS)
