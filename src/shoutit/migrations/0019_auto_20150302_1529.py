# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('shoutit', '0018_auto_20150227_2025'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='profile',
            name='isSMS',
        ),
        migrations.AlterField(
            model_name='notification',
            name='type',
            field=models.IntegerField(default=0, choices=[(0, b'listen'), (1, b'message'), (2, b'Experience'), (3, b'Experience Shared'), (4, b'Comment')]),
            preserve_default=True,
        ),
    ]
