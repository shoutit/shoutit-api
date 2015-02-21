# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('shoutit', '0003_auto_20150216_1311'),
    ]

    operations = [
        migrations.AlterField(
            model_name='profile',
            name='video',
            field=models.OneToOneField(null=True, on_delete=django.db.models.deletion.SET_NULL, default=None, blank=True, to='shoutit.Video'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='user',
            name='first_name',
            field=models.CharField(blank=True, max_length=30, verbose_name='first name', validators=[django.core.validators.MinLengthValidator(2)]),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='user',
            name='last_name',
            field=models.CharField(blank=True, max_length=30, verbose_name='last name', validators=[django.core.validators.MinLengthValidator(2)]),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='video',
            name='duration',
            field=models.IntegerField(),
            preserve_default=True,
        ),
    ]
