# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shoutit', '0066_auto_20160227_1733'),
    ]

    operations = [
        migrations.AddField(
            model_name='item',
            name='available_count',
            field=models.PositiveSmallIntegerField(default=1),
        ),
        migrations.AddField(
            model_name='item',
            name='is_sold',
            field=models.BooleanField(default=False, db_index=True),
        ),
    ]
