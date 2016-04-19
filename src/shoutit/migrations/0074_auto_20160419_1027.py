# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shoutit', '0073_auto_20160415_1506'),
    ]

    operations = [
        migrations.AlterField(
            model_name='notification',
            name='type',
            field=models.IntegerField(default=0, choices=[(0, 'new_listen'), (1, 'new_message'), (2, 'broadcast'), (3, 'profile_update'), (4, 'conversation_update'), (5, 'new_read_by'), (6, 'stats_update')]),
        ),
    ]
