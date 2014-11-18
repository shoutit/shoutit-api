import os
from django.db.models.signals import post_syncdb
from django.db import connection
from django.conf import settings
import apps.shoutit.models


def custom_sql(sender, **kwargs):
    print "Adding Shoutit custom SQL functions (deploy.sql) ..."
    cursor = connection.cursor()
    cursor.execute(open(os.path.join(settings.BASE_DIR, 'deploy_scripts', 'deploy.sql'), 'r').read())


post_syncdb.connect(custom_sql, sender=apps.shoutit.models)
