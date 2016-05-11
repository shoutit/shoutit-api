# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shoutit', '0005_auto_20160510_2017'),
    ]

    operations = [
        migrations.AlterField(
            model_name='report',
            name='type',
            field=models.IntegerField(default=0, choices=[(0, 'general'), (1, 'web_app'), (2, 'iphone_app'), (3, 'android_app'), (4, 'profile'), (5, 'shout'), (6, 'conversation')]),
        ),
    ]
