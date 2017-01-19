# -*- coding: utf-8 -*-
"""

"""
from __future__ import unicode_literals, print_function

import os
import sys
import datetime
import dotenv
from kitchen.text.converters import getwriter

# very important when printing unicode strings
sys.stdout = getwriter('utf8')(sys.stdout)
sys.stderr = getwriter('utf8')(sys.stderr)

SRC_DIR = os.path.dirname(os.path.realpath(__file__))
SHOUTIT_ENV = os.environ.get('SHOUTIT_ENV', 'local')

# Local or Dev or Prod
LOCAL = SHOUTIT_ENV == 'local'

# Read env variables from .env file based on `SHOUTIT_ENV`
env_file = os.path.join(SRC_DIR, 'configs', SHOUTIT_ENV + '.env')
dotenv.read_dotenv(env_file)


def info(*args):
    _now = datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
    print("[%s] [INFO]:" % _now, *args, file=sys.stderr)
