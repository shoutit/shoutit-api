# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, connection
from shoutit.models import User


def nothing():
    pass


def unify_ids(apps, schema_editor):
    cursor = connection.cursor()
    for record in User.objects.all().values('id', 'profile__id'):
        try:
            user_id = record['id']
            ap_id = record['profile__id']
        except Exception as e:
            print "Error unifying ids for User: %s" % record
            print str(e)
            continue

        # Update id in Profile / Page to match user id
        cursor.execute('update shoutit_profile set id = %s where id = %s', [user_id, ap_id])

        # Update object_id in Stream to match user id
        cursor.execute('update shoutit_stream set object_id = %s where object_id = %s', [user_id, ap_id])


class Migration(migrations.Migration):

    dependencies = [
        ('shoutit', '0046_delete_events'),
    ]

    operations = [
        migrations.RunPython(unify_ids, nothing)
    ]
