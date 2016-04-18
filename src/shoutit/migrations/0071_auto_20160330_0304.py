# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shoutit', '0070_device'),
    ]

    operations = [
        migrations.RenameField(
            model_name='notification',
            old_name='FromUser',
            new_name='from_user',
        ),
        migrations.RenameField(
            model_name='notification',
            old_name='ToUser',
            new_name='to_user',
        ),
        migrations.AlterField(
            model_name='notification',
            name='type',
            field=models.IntegerField(default=0, choices=[(0, 'new_listen'), (1, 'new_message'), (2, 'broadcast'), (3, 'profile_update'), (4, 'conversation_update'), (5, 'Experience'), (6, 'Experience Shared'), (7, 'Comment')]),
        ),
    ]
