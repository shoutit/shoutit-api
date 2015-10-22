# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations, connection
from shoutit.models import Profile, User


def unify_ids(apps, schema_editor):
    cursor = connection.cursor()
    for user in User.objects.all().select_related('profile', 'page'):
        try:
            user_id = user.id.hex
            ap_id = user.ap.id.hex
            stream_id = user.ap.stream.id.hex
            assert user_id == ap_id == stream_id
        except AssertionError:
            pass
            continue
        except Exception as e:
            print "Error unifying ids for User: %s" % user
            print str(e)
            continue

        # Update id in Profile / Page to match user id
        if isinstance(user.ap, Profile):
            cursor.execute('update shoutit_profile set id = %s where id = %s', [user_id, ap_id])
        else:
            cursor.execute('update shoutit_page set id = %s where id = %s', [user_id, ap_id])

        # Update object_id in Stream to match user id
        cursor.execute('update shoutit_stream set object_id = %s where object_id = %s', [user_id, ap_id])

        # Update id in Stream to match user id
        cursor.execute('update shoutit_stream set id = %s where id = %s', [user_id, stream_id])

        # Update stream_id in Listen to match user id
        cursor.execute('update shoutit_listen set stream_id = %s where stream_id = %s', [user_id, stream_id])


class Migration(migrations.Migration):

    dependencies = [
        ('shoutit', '0046_auto_20151016_1838'),
    ]

    operations = [
        migrations.RunPython(unify_ids)
    ]
