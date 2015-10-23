# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('shoutit', '0038_auto_20151011_1948'),
    ]

    operations = [
        migrations.AlterField(
            model_name='stream',
            name='type',
            field=models.SmallIntegerField(db_index=True, choices=[(0, 'Profile'), (1, 'Tag'), (2, 'Page'), (3, 'Related'), (4, 'Recommended')]),
        ),
    ]
