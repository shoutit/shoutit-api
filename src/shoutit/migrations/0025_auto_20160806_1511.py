# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shoutit', '0024_smsinvitation2'),
    ]

    operations = [
        migrations.AddField(
            model_name='smsinvitation',
            name='link',
            field=models.CharField(default='', max_length=200, blank=True),
        ),
        migrations.AddField(
            model_name='smsinvitation',
            name='source',
            field=models.CharField(default='', max_length=20, db_index=True, blank=True),
        ),
    ]
