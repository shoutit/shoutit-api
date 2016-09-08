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
            name='unread_conversations_count',
            field=models.IntegerField(default=0, verbose_name='unread conversations count'),
        ),
    ]
