# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('shoutit', '0023_auto_20150304_1322'),
    ]

    operations = [
        migrations.AlterField(
            model_name='featuredtag',
            name='rank',
            field=models.PositiveSmallIntegerField(validators=[django.core.validators.MinValueValidator(1)]),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='featuredtag',
            unique_together=set([('country', 'city', 'rank')]),
        ),
    ]
