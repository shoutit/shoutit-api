from __future__ import unicode_literals

import multiprocessing
import os
import sys

# include src dir in sys.path a.k.a PYTHONPATH to be able to use env_settings.
sys.path.append(os.path.dirname(os.path.realpath(__file__)))
from settings_env import *  # NOQA

if LOCAL:
    bind = '0.0.0.0:8000'
    workers = 1
    timeout = 5 * 60
else:
    bind = '0.0.0.0:8001'
    workers = multiprocessing.cpu_count() * 2 + 1
    max_requests = 1000

errorlog = '/dev/stderr'
accesslog = '/dev/stdout'
loglevel = 'info'

preload_app = True
proc_name = 'shoutit-api-' + SHOUTIT_ENV

# def when_ready(server):
#     from django import setup
#     from django.core.management import call_command
#     os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")
#     setup()
#     call_command('validate')
