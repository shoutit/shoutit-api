# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.contrib.postgres.fields
import datetime


class Migration(migrations.Migration):

    dependencies = [
        ('shoutit', '0053_conversation_admins'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='linkedfacebookaccount',
            name='expires',
        ),
        migrations.AddField(
            model_name='linkedfacebookaccount',
            name='expires_at',
            field=models.DateTimeField(default=datetime.datetime(2015, 12, 4, 20, 4, 18, 607000)),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='linkedfacebookaccount',
            name='scopes',
            field=django.contrib.postgres.fields.ArrayField(default=['public_profile', 'email'], base_field=models.CharField(max_length=50), size=None),
        ),
    ]
