# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import re
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('shoutit', '0028_auto_20150309_1529'),
    ]

    operations = [
        migrations.AlterField(
            model_name='tag',
            name='name',
            field=models.CharField(db_index=True, unique=True, max_length=30, validators=[django.core.validators.MinLengthValidator(2), django.core.validators.RegexValidator(re.compile(b'[0-9a-z-]{2,30}'), b'Enter a valid tag.', b'invalid')]),
            preserve_default=True,
        ),
    ]
