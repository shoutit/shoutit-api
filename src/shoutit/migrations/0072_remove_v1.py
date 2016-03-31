# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models

from shoutit.models import Permission


def remove_unused_perms(apps, schema_editor):
    names = ['SHOUT_EXPERIENCE', 'SHARE_EXPERIENCE', 'COMMENT_ON_POST', 'SHOUT_DEAL']
    Permission.objects.filter(name__in=names).delete()
    Permission.objects.filter(name='LISTEN_TO_USER').update(name='LISTEN_TO_PROFILE')


def reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('shoutit', '0071_auto_20160330_0304'),
    ]

    operations = [
        migrations.AlterField(
            model_name='notification',
            name='type',
            field=models.IntegerField(default=0, choices=[(0, 'new_listen'), (1, 'new_message'), (2, 'broadcast'), (3, 'profile_update'), (4, 'conversation_update'), (5, 'new_read_by')]),
        ),
        migrations.AlterField(
            model_name='post',
            name='type',
            field=models.IntegerField(default=0, db_index=True, choices=[(0, 'request'), (1, 'offer')]),
        ),
        migrations.AlterField(
            model_name='report',
            name='type',
            field=models.IntegerField(default=0, choices=[(0, 'general'), (1, 'web_app'), (2, 'iphone_app'), (3, 'android_app'), (4, 'profile'), (5, 'shout')]),
        ),
        migrations.RunPython(remove_unused_perms, reverse)
    ]
