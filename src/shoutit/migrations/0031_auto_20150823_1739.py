# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('shoutit', '0030_googlelocation'),
    ]

    operations = [
        migrations.AlterField(
            model_name='featuredtag',
            name='postal_code',
            field=models.CharField(db_index=True, max_length=30, blank=True),
        ),
        migrations.AlterField(
            model_name='googlelocation',
            name='postal_code',
            field=models.CharField(db_index=True, max_length=30, blank=True),
        ),
        migrations.AlterField(
            model_name='post',
            name='postal_code',
            field=models.CharField(db_index=True, max_length=30, blank=True),
        ),
        migrations.AlterField(
            model_name='predefinedcity',
            name='postal_code',
            field=models.CharField(db_index=True, max_length=30, blank=True),
        ),
        migrations.AlterField(
            model_name='profile',
            name='postal_code',
            field=models.CharField(db_index=True, max_length=30, blank=True),
        ),
        migrations.AlterField(
            model_name='sharedlocation',
            name='postal_code',
            field=models.CharField(db_index=True, max_length=30, blank=True),
        ),
    ]
