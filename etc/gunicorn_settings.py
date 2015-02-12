from etc.env_settings import *

if LOCAL:
    bind = '0.0.0.0:8000'
    workers = 1
    errorlog = '-'
    accesslog = '-'
else:
    bind = '0.0.0.0:8001'
    workers = 1
    errorlog = '-'
    accesslog = '-'

loglevel = 'info'


def when_ready(server):
    from django import setup
    from django.core.management import call_command
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")
    setup()
    call_command('validate')
