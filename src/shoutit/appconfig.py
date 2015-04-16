import os
from django.apps import AppConfig
from django.db import connection
from django.conf import settings


def custom_sql(sender, **kwargs):
    if sender.name == 'shoutit':
        print "Adding Shoutit custom SQL functions (deploy.sql) ..."
        cursor = connection.cursor()
        cursor.execute(open(os.path.join(settings.DJANGO_DIR, 'sql_scripts', 'scripts.sql'), 'r').read())


class ShoutitConfig(AppConfig):
    name = 'shoutit'
    label = 'shoutit'
    verbose_name = "Shoutit"

    def ready(self):
        # scripts.sql is empty finally! :)
        # post_migrate.connect(custom_sql, sender=self)
        pass
