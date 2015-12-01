# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.contrib.postgres.fields


class Migration(migrations.Migration):

    dependencies = [
        ('shoutit', '0052_tags2'),
    ]

    operations = [
        migrations.AddField(
            model_name='conversation',
            name='admins',
            field=django.contrib.postgres.fields.ArrayField(default=list, size=None, base_field=models.UUIDField(), blank=True),
        ),
    ]
