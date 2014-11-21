import os
from south.signals import post_migrate
from django.db import connection
from django.conf import settings


def custom_sql(app, **kwargs):
    if app == 'shoutit':
        print "Adding Shoutit custom SQL functions (deploy.sql) ..."
        cursor = connection.cursor()
        cursor.execute(open(os.path.join(settings.BASE_DIR, 'deploy_scripts', 'deploy.sql'), 'r').read())


post_migrate.connect(custom_sql)
