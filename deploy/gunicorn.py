import os

SHOUTIT_ENV = os.environ.get('SHOUTIT_ENV', 'development')

if SHOUTIT_ENV.lower() in ['development', 'stage']:
    workers = 1
    timeout = 5 * 60
else:
    workers = 4
    max_requests = 1000
    timeout = 60

bind = '0.0.0.0:8001'
errorlog = accesslog = '-'
loglevel = 'info'
preload_app = True
proc_name = 'shoutit-api-' + SHOUTIT_ENV
