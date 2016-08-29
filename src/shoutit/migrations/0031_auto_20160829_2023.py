# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shoutit', '0030_auth_token'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='credit',
            field=models.PositiveIntegerField(default=0, verbose_name='credit'),
        ),
        migrations.AddField(
            model_name='user',
            name='unread_conversations_count',
            field=models.PositiveIntegerField(default=0, verbose_name='unread conversations count'),
        ),
        migrations.AddField(
            model_name='user',
            name='unread_notifications_count',
            field=models.PositiveIntegerField(default=0, verbose_name='unread notifications count'),
        ),
    ]
