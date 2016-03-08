# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shoutit', '0067_auto_20160305_1715'),
    ]

    operations = [
        migrations.AddField(
            model_name='shout',
            name='mobile',
            field=models.CharField(default='', max_length=20, blank=True),
        ),
    ]
