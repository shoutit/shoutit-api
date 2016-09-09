# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shoutit', '0032_user_unread_notifications_count'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='credit',
            field=models.IntegerField(default=0, verbose_name='aggregated credits'),
        ),
    ]
