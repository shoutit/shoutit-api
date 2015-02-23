# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.core.validators
import re
import common.utils


class Migration(migrations.Migration):

    dependencies = [
        ('shoutit', '0009_auto_20150223_1326'),
    ]

    operations = [
        migrations.AddField(
            model_name='messageattachment',
            name='type',
            field=models.SmallIntegerField(null=True, choices=[(0, b'shout'), (1, b'location')]),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='user',
            name='username',
            field=models.CharField(help_text='Required. 2 to 30 characters and can only contain A-Z, a-z, 0-9, and periods (.)', unique=True, max_length=30, verbose_name='username', validators=[django.core.validators.RegexValidator(re.compile(b'[0-9a-zA-Z.]{2,30}'), 'Enter a valid username.', b'invalid'), django.core.validators.MinLengthValidator(2), common.utils.AllowedUsernamesValidator()]),
            preserve_default=True,
        ),
    ]