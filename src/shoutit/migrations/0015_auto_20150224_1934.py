# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('shoutit', '0014_auto_20150224_1638'),
    ]

    operations = [
        migrations.AlterField(
            model_name='sharedlocation',
            name='latitude',
            field=models.FloatField(validators=[django.core.validators.MaxValueValidator(90), django.core.validators.MinValueValidator(-90)]),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='sharedlocation',
            name='longitude',
            field=models.FloatField(validators=[django.core.validators.MaxValueValidator(180), django.core.validators.MinValueValidator(-180)]),
            preserve_default=True,
        ),
    ]
