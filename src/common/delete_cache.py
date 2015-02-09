import sys
import redis
from settings import CACHES
import re

regex = re.compile('^(?::\d:)?(user|session|apns|perma)')
for db in range(2):
    r = redis.StrictRedis(host=CACHES['default']['LOCATION'].split(':')[0], port=int(CACHES['default']['LOCATION'].split(':')[1]), db=db)
    [r.delete(k) for k in r.keys('*') if not regex.match(k)]

if len(sys.argv) > 1:
    regex = re.compile('^(?::\d:)?(' + '|'.join(sys.argv[1:]) + ')')
    for db in range(2):
        r = redis.StrictRedis(host=CACHES['default']['LOCATION'].split(':')[0], port=int(CACHES['default']['LOCATION'].split(':')[1]),
                              db=db)
        [r.delete(k) for k in r.keys('*') if regex.match(k)]
