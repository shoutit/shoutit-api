# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.core.validators


class Migration(migrations.Migration):
    dependencies = [
        ('shoutit', '0012_fix_location'),
    ]

    operations = [
        migrations.AddField(
            model_name='post',
            name='postal_code',
            field=models.CharField(db_index=True, max_length=10, blank=True),
        ),
        migrations.AddField(
            model_name='post',
            name='state',
            field=models.CharField(db_index=True, max_length=50, blank=True),
        ),
        migrations.AddField(
            model_name='predefinedcity',
            name='address',
            field=models.CharField(max_length=200, blank=True),
        ),
        migrations.AddField(
            model_name='predefinedcity',
            name='postal_code',
            field=models.CharField(db_index=True, max_length=10, blank=True),
        ),
        migrations.AddField(
            model_name='predefinedcity',
            name='state',
            field=models.CharField(db_index=True, max_length=50, blank=True),
        ),
        migrations.AddField(
            model_name='profile',
            name='address',
            field=models.CharField(max_length=200, blank=True),
        ),
        migrations.AddField(
            model_name='profile',
            name='postal_code',
            field=models.CharField(db_index=True, max_length=10, blank=True),
        ),
        migrations.AddField(
            model_name='profile',
            name='state',
            field=models.CharField(db_index=True, max_length=50, blank=True),
        ),
        migrations.AddField(
            model_name='sharedlocation',
            name='address',
            field=models.CharField(max_length=200, blank=True),
        ),
        migrations.AddField(
            model_name='sharedlocation',
            name='city',
            field=models.CharField(db_index=True, max_length=100, blank=True),
        ),
        migrations.AddField(
            model_name='sharedlocation',
            name='country',
            field=models.CharField(db_index=True, max_length=2, blank=True),
        ),
        migrations.AddField(
            model_name='sharedlocation',
            name='postal_code',
            field=models.CharField(db_index=True, max_length=10, blank=True),
        ),
        migrations.AddField(
            model_name='sharedlocation',
            name='state',
            field=models.CharField(db_index=True, max_length=50, blank=True),
        ),
        migrations.AlterField(
            model_name='post',
            name='address',
            field=models.CharField(max_length=200, blank=True),
        ),
        migrations.AlterField(
            model_name='post',
            name='city',
            field=models.CharField(db_index=True, max_length=100, blank=True),
        ),
        migrations.AlterField(
            model_name='post',
            name='country',
            field=models.CharField(db_index=True, max_length=2, blank=True),
        ),
        migrations.AlterField(
            model_name='post',
            name='latitude',
            field=models.FloatField(validators=[django.core.validators.MaxValueValidator(90),
                                                django.core.validators.MinValueValidator(-90)]),
        ),
        migrations.AlterField(
            model_name='post',
            name='longitude',
            field=models.FloatField(validators=[django.core.validators.MaxValueValidator(180),
                                                django.core.validators.MinValueValidator(-180)]),
        ),
        migrations.AlterField(
            model_name='predefinedcity',
            name='city',
            field=models.CharField(db_index=True, max_length=100, blank=True),
        ),
        migrations.AlterField(
            model_name='predefinedcity',
            name='country',
            field=models.CharField(db_index=True, max_length=2, blank=True),
        ),
        migrations.AlterField(
            model_name='predefinedcity',
            name='latitude',
            field=models.FloatField(validators=[django.core.validators.MaxValueValidator(90),
                                                django.core.validators.MinValueValidator(-90)]),
        ),
        migrations.AlterField(
            model_name='predefinedcity',
            name='longitude',
            field=models.FloatField(validators=[django.core.validators.MaxValueValidator(180),
                                                django.core.validators.MinValueValidator(-180)]),
        ),
        migrations.AlterField(
            model_name='profile',
            name='city',
            field=models.CharField(db_index=True, max_length=100, blank=True),
        ),
        migrations.AlterField(
            model_name='profile',
            name='country',
            field=models.CharField(db_index=True, max_length=2, blank=True),
        ),
        migrations.AlterField(
            model_name='profile',
            name='latitude',
            field=models.FloatField(validators=[django.core.validators.MaxValueValidator(90),
                                                django.core.validators.MinValueValidator(-90)]),
        ),
        migrations.AlterField(
            model_name='profile',
            name='longitude',
            field=models.FloatField(validators=[django.core.validators.MaxValueValidator(180),
                                                django.core.validators.MinValueValidator(-180)]),
        ),
    ]
