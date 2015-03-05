# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('shoutit', '0024_auto_20150304_1341'),
    ]

    operations = [
        migrations.AlterField(
            model_name='post',
            name='streams2_ids',
            field=models.CharField(default=b'', max_length=778, blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='trade',
            name='renewal_count',
            field=models.PositiveSmallIntegerField(default=0),
            preserve_default=True,
        ),
    ]
