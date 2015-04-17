# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.contrib.postgres.fields


class Migration(migrations.Migration):

    dependencies = [
        ('shoutit', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='storedimage',
            name='item',
        ),
        migrations.RemoveField(
            model_name='storedimage',
            name='shout',
        ),
        migrations.AddField(
            model_name='item',
            name='images',
            field=django.contrib.postgres.fields.ArrayField(null=True, base_field=models.URLField(), size=None),
        ),
        migrations.DeleteModel(
            name='StoredImage',
        ),
    ]
