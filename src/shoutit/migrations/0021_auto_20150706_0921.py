# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.contrib.postgres.fields


class Migration(migrations.Migration):

    dependencies = [
        ('shoutit', '0020_auto_20150619_1241'),
    ]

    operations = [
        migrations.AddField(
            model_name='messageattachment',
            name='images',
            field=django.contrib.postgres.fields.ArrayField(size=None, null=True, base_field=models.URLField(), blank=True),
        ),
        migrations.AddField(
            model_name='messageattachment',
            name='videos',
            field=models.ManyToManyField(to='shoutit.Video', blank=True),
        ),
        migrations.AlterField(
            model_name='messageattachment',
            name='type',
            field=models.SmallIntegerField(choices=[(0, 'shout'), (1, 'location'), (2, 'media')]),
        ),
        migrations.AlterField(
            model_name='notification',
            name='type',
            field=models.IntegerField(default=0, choices=[(0, 'new_listen'), (1, 'new_message'), (2, 'Experience'), (3, 'Experience Shared'), (4, 'Comment')]),
        ),
        migrations.AlterField(
            model_name='video',
            name='duration',
            field=models.PositiveIntegerField(),
        ),
    ]
