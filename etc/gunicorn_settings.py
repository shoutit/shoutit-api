# include the BACKEND_DIR in sys.path a.k.a PYTHONPATH to be able to use etc.env_settings for example.
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'src'))
from etc.env_settings import *

if LOCAL:
    bind = '0.0.0.0:8000'
    workers = 1
else:
    bind = '0.0.0.0:8001'
    workers = 1

accesslog = os.path.join(LOG_DIR, 'gunicorn.access')
errorlog = os.path.join(LOG_DIR, 'gunicorn.error')
loglevel = 'debug'


def when_ready(server):
    from django import setup
    from django.core.management import call_command
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")
    setup()
    call_command('validate')
