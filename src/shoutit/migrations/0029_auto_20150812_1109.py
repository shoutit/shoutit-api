# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.contrib.postgres.fields


class Migration(migrations.Migration):

    dependencies = [
        ('shoutit', '0028_smsinvitation_old_message'),
    ]

    operations = [
        migrations.AlterField(
            model_name='item',
            name='images',
            field=django.contrib.postgres.fields.ArrayField(default=list, size=None, base_field=models.URLField(), blank=True),
        ),
        migrations.AlterField(
            model_name='messageattachment',
            name='images',
            field=django.contrib.postgres.fields.ArrayField(default=list, size=None, base_field=models.URLField(), blank=True),
        ),
    ]
