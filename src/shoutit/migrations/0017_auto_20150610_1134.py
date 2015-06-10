# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('shoutit', '0016_auto_20150604_1729'),
    ]

    operations = [
        migrations.AddField(
            model_name='featuredtag',
            name='postal_code',
            field=models.CharField(db_index=True, max_length=10, blank=True),
        ),
        migrations.AddField(
            model_name='featuredtag',
            name='state',
            field=models.CharField(db_index=True, max_length=50, blank=True),
        ),
        migrations.AlterField(
            model_name='featuredtag',
            name='city',
            field=models.CharField(db_index=True, max_length=100, blank=True),
        ),
        migrations.AlterField(
            model_name='featuredtag',
            name='country',
            field=models.CharField(db_index=True, max_length=2, blank=True),
        ),
        migrations.AlterUniqueTogether(
            name='featuredtag',
            unique_together=set([('country', 'postal_code', 'state', 'city', 'rank')]),
        ),
    ]
