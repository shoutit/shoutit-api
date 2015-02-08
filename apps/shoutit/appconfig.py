import os
from django.apps import AppConfig
from django.db.models.signals import post_migrate
from django.db import connection
from django.conf import settings


# todo: remove and use data migrations instead
def custom_sql(sender, **kwargs):
    if sender.name == 'apps.shoutit':
        print "Adding Shoutit custom SQL functions (deploy.sql) ..."
        cursor = connection.cursor()
        cursor.execute(open(os.path.join(settings.BASE_DIR, 'deploy_scripts', 'deploy.sql'), 'r').read())


class ShoutitConfig(AppConfig):
    name = 'apps.shoutit'
    label = 'shoutit'
    verbose_name = "Shoutit"

    def ready(self):
        post_migrate.connect(custom_sql, sender=self)
