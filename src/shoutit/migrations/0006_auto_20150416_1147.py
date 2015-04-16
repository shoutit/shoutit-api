# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('shoutit', '0005_auto_20150416_1013'),
    ]

    operations = [
        migrations.AlterField(
            model_name='report',
            name='text',
            field=models.TextField(max_length=300, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='report',
            name='type',
            field=models.IntegerField(default=0, choices=[(0, 'general'), (1, 'web_app'), (2, 'iphone_app'), (3, 'android_app'), (4, 'user'), (5, 'shout'), (6, 'business'), (7, 'item'), (8, 'experience'), (9, 'comment')]),
        ),
    ]
