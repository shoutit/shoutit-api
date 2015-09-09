# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('shoutit', '0033_auto_20150831_0132'),
    ]

    operations = [
        migrations.AlterField(
            model_name='item',
            name='description',
            field=models.TextField(max_length=10000),
        ),
        migrations.AlterField(
            model_name='post',
            name='text',
            field=models.TextField(max_length=10000, blank=True),
        ),
    ]
