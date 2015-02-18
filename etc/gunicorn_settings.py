import sys
import os

# include current dir in sys.path a.k.a PYTHONPATH to be able to use env_settings.
me = os.path.realpath(__file__)
etc = os.path.dirname(me)
sys.path.append(etc)

from env_settings import *

if LOCAL:
    bind = '0.0.0.0:8000'
    workers = 1
else:
    bind = '0.0.0.0:8001'
    workers = 1

errorlog = accesslog = '-'
loglevel = 'info'

check_config = False


# def when_ready(server):
#     from django import setup
#     from django.core.management import call_command
#     os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")
#     setup()
#     call_command('validate')
