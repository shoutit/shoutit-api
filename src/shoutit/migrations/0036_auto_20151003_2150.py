# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('shoutit', '0035_auto_20150930_2018'),
    ]

    operations = [
        migrations.AlterField(
            model_name='item',
            name='videos',
            field=models.ManyToManyField(related_name='items', to='shoutit.Video', blank=True),
        ),
    ]
