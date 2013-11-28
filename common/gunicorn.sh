#!/bin/bash
set -e
cd /home/django/Shout/
exec gunicorn_django -c gunicorn.conf
