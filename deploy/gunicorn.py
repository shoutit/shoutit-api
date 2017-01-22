import multiprocessing
import os

SHOUTIT_ENV = os.environ.get('SHOUTIT_ENV', 'local')

if SHOUTIT_ENV == 'local':
    workers = 1
    timeout = 5 * 60
else:
    workers = multiprocessing.cpu_count() * 2 + 1
    max_requests = 1000
    timeout = 60

bind = '0.0.0.0:8001'
errorlog = accesslog = '-'
loglevel = 'info'
preload_app = True
proc_name = 'shoutit-api-' + SHOUTIT_ENV
