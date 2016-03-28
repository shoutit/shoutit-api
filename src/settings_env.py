# -*- coding: utf-8 -*-
"""

"""
from __future__ import unicode_literals, print_function

import os
import sys

from django.utils import timezone
from kitchen.text.converters import getwriter

# very important when printing unicode strings
sys.stdout = getwriter('utf8')(sys.stdout)
sys.stderr = getwriter('utf8')(sys.stderr)

DJANGO_DIR = os.path.dirname(os.path.realpath(__file__))
API_DIR = os.path.dirname(DJANGO_DIR)
ENV = os.environ.get('ENV', 'shoutit_api_local')
LOG_DIR = os.path.join('/var', 'log', ENV)

if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

# Local or Dev or Prod
LOCAL = ENV == 'shoutit_api_local'
ON_SERVER = not LOCAL
DEV = ON_SERVER and ENV == 'shoutit_api_dev'
PROD = ON_SERVER and ENV == 'shoutit_api_prod'


def info(*args):
    _now = timezone.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
    print("[%s] [INFO]:" % _now, *args, file=sys.stderr)
