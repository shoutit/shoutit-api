# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shoutit', '0064_auto_20160226_1133'),
    ]

    operations = [
        migrations.AddField(
            model_name='googlelocation',
            name='is_indexed',
            field=models.BooleanField(default=False, db_index=True),
        ),
        migrations.AddField(
            model_name='shout',
            name='is_indexed',
            field=models.BooleanField(default=False, db_index=True),
        ),
    ]
