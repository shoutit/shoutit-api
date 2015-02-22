# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('shoutit', '0005_auto_20150221_1543'),
    ]

    operations = [
        migrations.AddField(
            model_name='post',
            name='streams2_ids',
            field=models.CharField(default=b'', max_length=740, blank=True),
            preserve_default=True,
        ),
    ]
