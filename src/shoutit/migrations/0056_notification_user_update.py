# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shoutit', '0055_post_published_on'),
    ]

    operations = [
        migrations.AlterField(
            model_name='notification',
            name='type',
            field=models.IntegerField(default=0, choices=[(0, 'new_listen'), (1, 'new_message'), (2, 'broadcast'), (3, 'user_update'), (4, 'Experience'), (5, 'Experience Shared'), (6, 'Comment')]),
        ),
    ]
