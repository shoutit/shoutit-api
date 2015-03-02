# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('shoutit', '0021_auto_20150302_1901'),
    ]

    operations = [
        migrations.RenameField(
            model_name='category',
            old_name='TopTag',
            new_name='main_tag',
        ),
        migrations.AlterField(
            model_name='category',
            name='name',
            field=models.CharField(unique=True, max_length=100, db_index=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='tag',
            name='image',
            field=models.CharField(max_length=1024, null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='tag',
            name='name',
            field=models.CharField(unique=True, max_length=100, db_index=True),
            preserve_default=True,
        ),
    ]
