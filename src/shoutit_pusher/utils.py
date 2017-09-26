# -*- coding: utf-8 -*-
"""

"""
from pusher import Pusher
from .settings import SHOUTIT_PUSHER_SETTINGS


pusher = Pusher(**SHOUTIT_PUSHER_SETTINGS)
