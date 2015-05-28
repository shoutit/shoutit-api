# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import re
import django.contrib.postgres.fields
import common.utils
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('shoutit', '0009_auto_20150528_1525'),
    ]

    operations = [
        migrations.AlterField(
            model_name='shout',
            name='tags',
            field=django.contrib.postgres.fields.ArrayField(base_field=models.CharField(help_text='Required. 2 to 30 characters and can only contain a-z, 0-9, and the dash (-)', unique=True, max_length=30, db_index=True, validators=[django.core.validators.MinLengthValidator(2), django.core.validators.RegexValidator(re.compile('^[0-9a-z-]+$'), 'Enter a valid tag.', 'invalid')]), size=None),
        ),
        migrations.AlterField(
            model_name='tag',
            name='name',
            field=models.CharField(help_text='Required. 2 to 30 characters and can only contain a-z, 0-9, and the dash (-)', unique=True, max_length=30, db_index=True, validators=[django.core.validators.MinLengthValidator(2), django.core.validators.RegexValidator(re.compile('^[0-9a-z-]+$'), 'Enter a valid tag.', 'invalid')]),
        ),
        migrations.AlterField(
            model_name='user',
            name='username',
            field=models.CharField(help_text='Required. 2 to 30 characters and can only contain A-Z, a-z, 0-9, and periods (.)', unique=True, max_length=30, verbose_name='username', validators=[django.core.validators.RegexValidator(re.compile('^[0-9a-zA-Z.]+$'), 'Enter a valid username.', 'invalid'), django.core.validators.MinLengthValidator(2), common.utils.AllowedUsernamesValidator()]),
        ),
    ]
