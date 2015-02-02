command = '/opt/myenv/bin/gunicorn'
pythonpath = '/opt/myenv/shoutit/shoutit_backend_dev'
bind = '0.0.0.0:8001'
workers = 1
errorlog = '-'
loglevel = 'debug'


def when_ready(server):
    from django.core.management import call_command
    call_command('validate')

