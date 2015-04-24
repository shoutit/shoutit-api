# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('shoutit', '0006_auto_20150423_2010'),
    ]

    operations = [
        migrations.AlterField(
            model_name='linkedfacebookaccount',
            name='facebook_id',
            field=models.CharField(unique=True, max_length=24, db_index=True),
        ),
        migrations.AlterField(
            model_name='linkedgoogleaccount',
            name='gplus_id',
            field=models.CharField(unique=True, max_length=64, db_index=True),
        ),
    ]
