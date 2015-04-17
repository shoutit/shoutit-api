# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.contrib.postgres.fields


class Migration(migrations.Migration):

    dependencies = [
        ('shoutit', '0002_auto_20150417_0113'),
    ]

    operations = [
        migrations.AlterField(
            model_name='item',
            name='images',
            field=django.contrib.postgres.fields.ArrayField(size=None, null=True, base_field=models.URLField(), blank=True),
        ),
    ]
