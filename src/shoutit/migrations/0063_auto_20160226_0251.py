# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.contrib.postgres.fields
import shoutit.models.tag


class Migration(migrations.Migration):

    dependencies = [
        ('shoutit', '0062_integer_price'),
    ]

    operations = [
        migrations.AlterField(
            model_name='item',
            name='description',
            field=models.TextField(default='', max_length=10000, blank=True),
        ),
        migrations.AlterField(
            model_name='item',
            name='name',
            field=models.CharField(default='', max_length=500, blank=True),
        ),
        migrations.AlterField(
            model_name='shout',
            name='tags',
            field=django.contrib.postgres.fields.ArrayField(default=list, size=None, base_field=shoutit.models.tag.ShoutitSlugField(help_text='Required. 1 to 30 characters and can only contain small letters, numbers, underscores or hyphens.'), blank=True),
        ),
    ]
