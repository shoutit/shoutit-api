# -*- coding: utf-8 -*-
"""

"""
from __future__ import unicode_literals, print_function
import os
import sys

DJANGO_DIR = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
API_DIR = os.path.dirname(DJANGO_DIR)
ENV_DIR = os.path.dirname(API_DIR)
ENV = os.path.basename(ENV_DIR)
LOG_DIR = os.path.join(ENV_DIR, 'log')

# Local or Dev or Prod
LOCAL = ENV == 'shoutit_api_local'
ON_SERVER = not LOCAL
DEV = ON_SERVER and ENV == 'shoutit_api_dev'
PROD = ON_SERVER and ENV == 'shoutit_api_prod'


def info(*args):
    print("[INFO]  ", *args, file=sys.stderr)