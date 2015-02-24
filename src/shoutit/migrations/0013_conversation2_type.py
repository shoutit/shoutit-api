# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('shoutit', '0012_auto_20150223_2057'),
    ]

    operations = [
        migrations.AddField(
            model_name='conversation2',
            name='type',
            field=models.SmallIntegerField(default=1, choices=[(0, b'chat'), (1, b'about_shout')]),
            preserve_default=False,
        ),
    ]
