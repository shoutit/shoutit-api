# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('shoutit', '0011_auto_20150223_1924'),
    ]

    operations = [
        migrations.AlterField(
            model_name='messageattachment',
            name='type',
            field=models.SmallIntegerField(choices=[(0, b'shout'), (1, b'location')]),
            preserve_default=True,
        ),
    ]
