# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('shoutit', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='is_test',
            field=models.BooleanField(default=False, help_text='Designates whether this user is a test user.', verbose_name='testuser status'),
        ),
        migrations.AddField(
            model_name='user',
            name='type',
            field=models.PositiveSmallIntegerField(default=0, db_index=True, choices=[(0, 'Profile'), (1, 'Page')]),
        ),
    ]
