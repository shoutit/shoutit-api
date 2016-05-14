# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('shoutit', '0009_shout_updates'),
    ]

    operations = [
        migrations.AddField(
            model_name='notification',
            name='expires_at',
            field=models.DateTimeField(db_index=True, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='notification',
            name='from_user',
            field=models.ForeignKey(related_name='+', blank=True, to=settings.AUTH_USER_MODEL, null=True),
        ),
        migrations.AlterField(
            model_name='notification',
            name='type',
            field=models.IntegerField(choices=[(0, 'new_listen'), (1, 'new_message'), (2, 'broadcast'), (3, 'profile_update'), (4, 'conversation_update'), (5, 'new_read_by'), (6, 'stats_update'), (7, 'video_call'), (8, 'missed_video_call')]),
        ),
        migrations.AlterField(
            model_name='shout',
            name='expires_at',
            field=models.DateTimeField(db_index=True, null=True, blank=True),
        ),
    ]
